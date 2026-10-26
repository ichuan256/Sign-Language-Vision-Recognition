#include "kp_vector.hpp"
#include "kp_sigmoid_lut.hpp"
#include "kp_vector_math.hpp"
int kp_vector(const short* a,const short* b,short* out,
              int count,int operation,int shift,int alpha,int beta,int limit,int kernel) {
#pragma HLS INTERFACE m_axi port=a offset=slave bundle=input_a depth=262144 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=b offset=slave bundle=input_b depth=65536 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=out offset=slave bundle=output_data depth=65536 max_write_burst_length=64
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
    if(count<1 || count>65536 || operation<0 || operation>5 || shift<-31 || shift>47)return 1;
    if(alpha<-31 || alpha>47 || beta<0 || beta>31)return 2;
    if(operation==KP_ADD && (alpha<0 || alpha>31))return 3;
    if(operation==KP_MAX && (kernel<1 || kernel>16 || count*kernel>262144))return 4;
    if(operation==KP_MEAN49 && (kernel!=49 || count>262144/49))return 5;
    if(operation==KP_ADD) {
        ADD:for(int i=0;i<count;++i) {
#pragma HLS PIPELINE II=1
            long long sum=static_cast<long long>(a[i])*(1LL<<alpha)+static_cast<long long>(b[i])*(1LL<<beta);
            out[i]=scale(sum,shift);
        }
    } else if(operation==KP_RELU) {
        RELU:for(int i=0;i<count;++i) {
#pragma HLS PIPELINE II=1
            long long x=a[i];if(x<0)x=0;if(limit>=0 && x>limit)x=limit;out[i]=scale(x,shift);
        }
    } else if(operation==KP_SCALE) {
        SCALE:for(int i=0;i<count;++i) {
#pragma HLS PIPELINE II=1
            out[i]=scale(a[i],shift);
        }
    } else if(operation==KP_MAX && kernel==4) {
        POOL4:for(int i=0;i<count;++i) {
#pragma HLS PIPELINE II=4
            short x0=a[i*4],x1=a[i*4+1],x2=a[i*4+2],x3=a[i*4+3];
            short p=x0>x1?x0:x1,q=x2>x3?x2:x3;out[i]=scale(p>q?p:q,shift);
        }
    } else {
        OTHER:for(int i=0;i<count;++i) {
#pragma HLS PIPELINE off
            if(operation==KP_MAX) {
                short maximum=-32768;
                for(int k=0;k<kernel;++k)if(a[i*kernel+k]>maximum)maximum=a[i*kernel+k];
                out[i]=scale(maximum,shift);
            } else if(operation==KP_MEAN49) {
                long long sum=0;for(int k=0;k<49;++k)sum+=a[i*49+k];out[i]=mean49(sum,shift);
            } else {
                int index=scale(a[i],shift);if(index<-512)index=-512;if(index>512)index=512;
                out[i]=scale(KP_SIGMOID_LUT[index+512],alpha);
            }
        }
    }
    return 0;
}
