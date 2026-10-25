#include "kp_vector.hpp"
#include "kp_sigmoid_lut.hpp"

static short saturated(long long value) {
    if (value>32767) return 32767;
    if (value<-32768) return -32768;
    return short(value);
}
static short scale(long long value,int shift) {
    bool negative=value<0;
    unsigned long long magnitude=negative ? -value : value;
    if (shift<0) {
        int left=-shift;
        unsigned long long bound=(negative ? 32768ULL : 32767ULL)>>left;
        if (magnitude>bound) return negative ? -32768 : 32767;
        magnitude <<= left;
    } else if (shift>0) {
        unsigned long long q=magnitude>>shift;
        unsigned long long r=magnitude&((1ULL<<shift)-1);
        unsigned long long half=1ULL<<(shift-1);
        if (r>half || (r==half && (q&1))) ++q;
        magnitude=q;
    }
    return saturated(negative ? -static_cast<long long>(magnitude) : static_cast<long long>(magnitude));
}
static short mean49(long long sum,int shift) {
    bool negative=sum<0;
    unsigned long long magnitude=negative ? -sum : sum;
    unsigned long long denominator=49;
    if (shift<0) magnitude <<= -shift;
    else denominator <<= shift;
    unsigned long long q=magnitude/denominator;
    unsigned long long r=magnitude%denominator;
    if (r>denominator-r || (r==denominator-r && (q&1))) ++q;
    return saturated(negative ? -static_cast<long long>(q) : static_cast<long long>(q));
}

int kp_vector(const short* a,const short* b,short* out,
              int count,int operation,int shift,int alpha,int beta,int limit,int kernel) {
#pragma HLS INTERFACE m_axi port=a offset=slave bundle=input_a depth=262144 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=b offset=slave bundle=input_b depth=4096 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=out offset=slave bundle=output_data depth=4096 max_write_burst_length=64
#pragma HLS INTERFACE s_axilite port=a bundle=control
#pragma HLS INTERFACE s_axilite port=b bundle=control
#pragma HLS INTERFACE s_axilite port=out bundle=control
#pragma HLS INTERFACE s_axilite port=count bundle=control
#pragma HLS INTERFACE s_axilite port=operation bundle=control
#pragma HLS INTERFACE s_axilite port=shift bundle=control
#pragma HLS INTERFACE s_axilite port=alpha bundle=control
#pragma HLS INTERFACE s_axilite port=beta bundle=control
#pragma HLS INTERFACE s_axilite port=limit bundle=control
#pragma HLS INTERFACE s_axilite port=kernel bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    if (count<1 || count>4096 || operation<0 || operation>5 || shift<-31 || shift>47) return 1;
    if (alpha<-31 || alpha>47 || beta<0 || beta>31) return 2;
    if (operation==KP_ADD && (alpha<0 || alpha>31)) return 3;
    if (operation==KP_MAX && (kernel<1 || kernel>16)) return 4;
    if (operation==KP_MEAN49 && kernel!=49) return 5;
    ELEMENTS: for (int i=0;i<count;++i) {
#pragma HLS PIPELINE off
#pragma HLS LOOP_TRIPCOUNT min=1 max=4096 avg=1024
        short value=0;
        if (operation==KP_ADD) {
            long long sum=static_cast<long long>(a[i])*(1LL<<alpha)+static_cast<long long>(b[i])*(1LL<<beta);
            value=scale(sum,shift);
        } else if (operation==KP_RELU) {
            long long x=a[i];
            if (x<0) x=0;
            if (limit>=0 && x>limit) x=limit;
            value=scale(x,shift);
        } else if (operation==KP_MAX) {
            short maximum=-32768;
            POOL: for (int k=0;k<kernel;++k) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=16 avg=4
                if (a[i*kernel+k]>maximum) maximum=a[i*kernel+k];
            }
            value=scale(maximum,shift);
        } else if (operation==KP_MEAN49) {
            long long sum=0;
            MEAN: for (int k=0;k<49;++k) sum+=a[i*49+k];
            value=mean49(sum,shift);
        } else if (operation==KP_SIGMOID) {
            int index=scale(a[i],shift);
            if (index<-512) index=-512;
            if (index>512) index=512;
            value=scale(KP_SIGMOID_LUT[index+512],alpha);
        } else value=scale(a[i],shift);
        out[i]=value;
    }
    return 0;
}
