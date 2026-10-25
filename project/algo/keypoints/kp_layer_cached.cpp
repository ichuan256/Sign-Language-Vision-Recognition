#include "kp_layer.hpp"
#include "kp_layer_math.hpp"

// Bounds are checked before these helpers are used. Narrow address arithmetic
// avoids spending multiple DSP48s on each generic 32-bit index multiplication.
static int tensor_address(int y,int x,int c,int width,int channels) {
    ap_uint<16> pixel=ap_uint<8>(y)*ap_uint<8>(width)+ap_uint<8>(x);
    ap_uint<20> address=pixel*ap_uint<10>(channels)+ap_uint<10>(c);
    return address.to_uint();
}
static int cache_address(int y,int x,int group,int width,int groups) {
    ap_uint<12> pixel=ap_uint<4>(y)*ap_uint<8>(width)+ap_uint<8>(x);
    ap_uint<18> address=pixel*ap_uint<6>(groups)+ap_uint<6>(group);
    return address.to_uint();
}
static int weight_address(int k,int channels,int c) {
    ap_uint<20> address=ap_uint<10>(k)*ap_uint<10>(channels)+ap_uint<10>(c);
    return address.to_uint();
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
    int groups=(ci+15)/16;
    int max_rows=((oh<4?oh:4)-1)*sy+kh;
    if (ih*iw*ci>802816 || oh*ow*co>802816 || (dw && ci!=co) || (!dw && kh*kw*ci>1024)) return 2;
    if (max_rows*iw*groups>4096 || (oh<4?oh:4)*ow*co>32768 || (!dw && kh*kw*ci*co>451584)) return 4;
    for (int c=0;c<co;++c) {
        if (shift[c]<-31 || shift[c]>47 || bias[c]>=(1LL<<47) || bias[c]<-(1LL<<47)) return 3;
    }
    // 128 KiB, 16 independent channel banks; input channels padded only on chip.
    ap_int<16> cache[4096][16];
#pragma HLS ARRAY_PARTITION variable=cache complete dim=2
#pragma HLS BIND_STORAGE variable=cache type=ram_2p impl=bram
    ap_int<16> output_cache[32768];
#pragma HLS BIND_STORAGE variable=output_cache type=ram_2p impl=bram
    ap_int<16> weights[1024][16];
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_2p impl=bram
    ap_int<48> biases[16];signed char shifts[16];
#pragma HLS ARRAY_PARTITION variable=biases complete
#pragma HLS ARRAY_PARTITION variable=shifts complete
    ROW_TILES: for (int ty=0;ty<oh;ty+=4) {
        int rows=oh-ty<4?oh-ty:4,load_rows=(rows-1)*sy+kh;
        CLEAR_CACHE: for (int index=0;index<load_rows*iw*groups;++index) {
#pragma HLS PIPELINE II=1
            for(int lane=0;lane<16;++lane) {
#pragma HLS UNROLL
                cache[index][lane]=0;
            }
        }
        LOAD_Y: for (int y=0;y<load_rows;++y) {
            int iy=(ap_uint<8>(ty)*ap_uint<2>(sy)).to_int()-py+y;
            if(iy>=0 && iy<ih) {
                int base=tensor_address(iy,0,0,iw,ci),length=iw*ci;
                ap_uint<10> channel=0,last=ci-1;ap_uint<8> column=0;
                LOAD_ROW_BURST: for(int index=0;index<length;++index) {
#pragma HLS PIPELINE II=1
#pragma HLS DEPENDENCE variable=cache inter false
                    // Simple forward DDR access permits a single pipelined burst.
                    // Every iteration writes a distinct bank/address; padding was cleared above.
                    cache[cache_address(y,column.to_uint(),channel.to_uint()/16,iw,groups)][channel.to_uint()%16]=a[base+index];
                    if(channel==last){channel=0;++column;}else ++channel;
                }
            }
        }
        CHANNEL_BLOCKS: for (int cb=0;cb<co;cb+=16) {
            int n=co-cb<16?co-cb:16;
            for (int c=0;c<16;++c) {
#pragma HLS PIPELINE II=1
                biases[c]=c<n?bias[cb+c]:0;shifts[c]=c<n?shift[cb+c]:0;
            }
            int depth=dw?kh*kw:kh*kw*ci;
            for (int k=0;k<depth;++k) {
                for (int c=0;c<16;++c) {
#pragma HLS PIPELINE II=1
                    weights[k][c]=c<n?b[weight_address(k,co,cb+c)]:0;
                }
            }
            OUTPUT_Y: for (int y=0;y<rows;++y) {
                OUTPUT_X: for (int x=0;x<ow;++x) {
                    ap_int<48> acc[16];
#pragma HLS ARRAY_PARTITION variable=acc complete
                    for (int c=0;c<16;++c) {
#pragma HLS UNROLL
                        acc[c]=biases[c];
                    }
                    if (dw) {
                        for (int ky=0;ky<kh;++ky) {
                            DW_KX: for (int kx=0;kx<kw;++kx) {
#pragma HLS PIPELINE II=1
                                int ix=(ap_uint<8>(x)*ap_uint<2>(sx)).to_int()+kx-px;
                                int cy=(ap_uint<2>(y)*ap_uint<2>(sy)).to_int()+ky;
                                int index=cache_address(cy,ix,cb/16,iw,groups);
                                for (int c=0;c<16;++c) {
#pragma HLS UNROLL
                                    ap_int<16> sample=ix>=0 && ix<iw ? cache[index][c] : ap_int<16>(0);
                                    ap_int<32> product=sample*weights[ky*kw+kx][c];
#pragma HLS BIND_OP variable=product op=mul impl=dsp latency=2
                                    ap_int<48> updated=acc[c]+product;
#pragma HLS BIND_OP variable=updated op=add impl=fabric latency=1
                                    acc[c]=updated;
                                }
                            }
                        }
                    } else {
                        for (int ky=0;ky<kh;++ky) {
                            for (int kx=0;kx<kw;++kx) {
                                int ix=(ap_uint<8>(x)*ap_uint<2>(sx)).to_int()+kx-px;
                                int cy=(ap_uint<2>(y)*ap_uint<2>(sy)).to_int()+ky;
                                INPUT_CHANNELS: for (int ic=0;ic<ci;++ic) {
#pragma HLS PIPELINE II=1
                                    int index=cache_address(cy,ix,ic/16,iw,groups);
                                    ap_int<16> sample=ix>=0 && ix<iw ? cache[index][ic%16] : ap_int<16>(0);
                                    ap_uint<10> k=(ap_uint<3>(ky)*ap_uint<3>(kw)+ap_uint<3>(kx))*ap_uint<10>(ci)+ap_uint<10>(ic);
                                    for (int c=0;c<16;++c) {
#pragma HLS UNROLL
                                        ap_int<32> product=sample*weights[k][c];
#pragma HLS BIND_OP variable=product op=mul impl=dsp latency=2
                                        ap_int<48> updated=acc[c]+product;
#pragma HLS BIND_OP variable=updated op=add impl=fabric latency=1
                                        acc[c]=updated;
                                    }
                                }
                            }
                        }
                    }
                    for (int c=0;c<n;++c) {
#pragma HLS PIPELINE II=1
                        output_cache[tensor_address(y,x,cb+c,ow,co)]=finish(acc[c],shifts[c],relu,rs,limit);
                    }
                }
            }
        }
        int output_base=tensor_address(ty,0,0,ow,co),output_length=rows*ow*co;
        WRITE_TILE_BURST: for(int index=0;index<output_length;++index) {
#pragma HLS PIPELINE II=1
            out[output_base+index]=output_cache[index];
        }
    }
    return 0;
}
