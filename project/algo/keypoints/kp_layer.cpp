#include "kp_layer.hpp"
#include <ap_int.h>

static short rounded(long long value,int shift) {
    bool neg=value<0;
    unsigned long long m=neg ? -value : value;
    if (shift<0) {
        int left=-shift;
        if (m>((neg ? 32768ULL : 32767ULL)>>left)) return neg ? -32768 : 32767;
        m <<= left;
    } else if (shift>0) {
        unsigned long long q=m>>shift,r=m&((1ULL<<shift)-1),half=1ULL<<(shift-1);
        if (r>half || (r==half && (q&1))) ++q;
        m=q;
    }
    long long result=neg ? -static_cast<long long>(m) : static_cast<long long>(m);
    return result>32767 ? 32767 : result<-32768 ? -32768 : short(result);
}
static short finish(ap_int<48> sum,int shift,int relu,int relu_shift,int limit) {
    // Keep the original intermediate saturation AND second rounding boundary.
    short value=rounded(sum.to_int64(),shift);
    if (relu) {
        if (value<0) value=0;
        if (limit>=0 && value>limit) value=short(limit);
        value=rounded(value,relu_shift);
    }
    return value;
}

int kp_layer(const short* a,const short* b,const long long* bias,
             const signed char* shift,short* out,const int* config) {
#pragma HLS INTERFACE m_axi port=a offset=slave bundle=activ depth=802816 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=b offset=slave bundle=weights depth=451584 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=bias offset=slave bundle=params depth=672
#pragma HLS INTERFACE m_axi port=shift offset=slave bundle=params depth=672
#pragma HLS INTERFACE m_axi port=config offset=slave bundle=params depth=16
#pragma HLS INTERFACE m_axi port=out offset=slave bundle=output_data depth=802816 max_write_burst_length=64
#pragma HLS INTERFACE s_axilite port=a bundle=control
#pragma HLS INTERFACE s_axilite port=b bundle=control
#pragma HLS INTERFACE s_axilite port=bias bundle=control
#pragma HLS INTERFACE s_axilite port=shift bundle=control
#pragma HLS INTERFACE s_axilite port=out bundle=control
#pragma HLS INTERFACE s_axilite port=config bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    int ih=config[0],iw=config[1],ci=config[2],oh=config[3],ow=config[4],co=config[5];
    int kh=config[6],kw=config[7],sy=config[8],sx=config[9],py=config[10],px=config[11];
    int dw=config[12],relu=config[13],rs=config[14],limit=config[15];
    if (ih<1 || ih>224 || iw<1 || iw>224 || oh<1 || oh>224 || ow<1 || ow>224 ||
        ci<1 || ci>672 || co<1 || co>672 || kh<1 || kh>5 || kw<1 || kw>5 ||
        sy<1 || sy>2 || sx<1 || sx>2 || py<0 || py>=kh || px<0 || px>=kw ||
        dw<0 || dw>1 || relu<0 || relu>1 || rs<-31 || rs>47 || limit<-1 || limit>32767) return 1;
    if (ih*iw*ci>802816 || oh*ow*co>802816 || (dw && ci!=co) || (!dw && kh*kw*ci>1024)) return 2;
    for (int c=0;c<co;++c) {
#pragma HLS PIPELINE off
        if (shift[c]<-31 || shift[c]>47 || bias[c]>= (1LL<<47) || bias[c]<-(1LL<<47)) return 3;
    }
    ap_int<16> weights[1024][16];
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_2p impl=bram
    ap_int<48> biases[16];
    signed char shifts[16];
#pragma HLS ARRAY_PARTITION variable=biases complete
#pragma HLS ARRAY_PARTITION variable=shifts complete
    CHANNEL_BLOCKS: for (int cb=0;cb<co;cb+=16) {
        int n=co-cb<16 ? co-cb : 16;
        for (int c=0;c<16;++c) {
#pragma HLS PIPELINE II=1
            biases[c]=c<n ? bias[cb+c] : 0;
            shifts[c]=c<n ? shift[cb+c] : 0;
        }
        int depth=dw ? kh*kw : kh*kw*ci;
        LOAD_WEIGHTS: for (int k=0;k<depth;++k) {
            for (int c=0;c<16;++c) {
#pragma HLS PIPELINE II=1
                weights[k][c]=c<n ? b[k*co+cb+c] : 0;
            }
        }
        OUTPUT_Y: for (int y=0;y<oh;++y) {
            OUTPUT_X: for (int x=0;x<ow;++x) {
                ap_int<48> acc[16];
#pragma HLS ARRAY_PARTITION variable=acc complete
                for (int c=0;c<16;++c) {
#pragma HLS UNROLL
                    acc[c]=biases[c];
                }
                for (int ky=0;ky<kh;++ky) {
                    for (int kx=0;kx<kw;++kx) {
                        int iy=y*sy+ky-py,ix=x*sx+kx-px;
                        bool inside=iy>=0 && iy<ih && ix>=0 && ix<iw;
                        if (dw) {
                            short samples[16];
#pragma HLS ARRAY_PARTITION variable=samples complete
                            for (int c=0;c<16;++c) {
#pragma HLS PIPELINE II=1
                                samples[c]=inside && c<n ? a[(iy*iw+ix)*ci+cb+c] : 0;
                            }
                            for (int c=0;c<16;++c) {
#pragma HLS UNROLL
                                ap_int<16> sample=samples[c];
                                ap_int<32> product=sample*weights[ky*kw+kx][c];
                                acc[c]+=product;
                            }
                        } else {
                            INPUT_CHANNELS: for (int ic=0;ic<ci;++ic) {
#pragma HLS PIPELINE II=1
                                ap_int<16> sample=inside ? a[(iy*iw+ix)*ci+ic] : 0;
                                int k=(ky*kw+kx)*ci+ic;
                                for (int c=0;c<16;++c) {
#pragma HLS UNROLL
                                    ap_int<32> product=sample*weights[k][c];
                                    acc[c]+=product;
                                }
                            }
                        }
                    }
                }
                STORE: for (int c=0;c<n;++c) {
#pragma HLS PIPELINE II=1
                    out[(y*ow+x)*co+cb+c]=finish(acc[c],shifts[c],relu,rs,limit);
                }
            }
        }
    }
    return 0;
}
