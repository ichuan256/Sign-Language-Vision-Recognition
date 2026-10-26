#pragma once
#include <hls_stream.h>
struct AccBlock {ap_int<48> values[16];};

static void produce_blocks(const ap_int<16> cache[4096][16],const ap_int<16> weights[1024][16],
    const ap_int<48> biases[16],hls::stream<AccBlock>& packets,
    int rows,int ow,int iw,int ci,int groups,int kh,int kw,int sy,int sx,int px,int dw,int cb) {
#pragma HLS INLINE off
#pragma HLS ARRAY_PARTITION variable=cache complete dim=2
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS ARRAY_PARTITION variable=biases complete
    int depth=shape_count(kh,kw,dw?1:ci);
    ap_uint<10> pixels=ap_uint<3>(rows)*ap_uint<8>(ow);
    ap_uint<21> total=pixels*ap_uint<11>(depth);
    ap_uint<10> k=0,last_k=depth-1,ic=0,last_ic=ci-1;
    ap_uint<3> ky=0,kx=0;ap_uint<8> x=0,last_x=ow-1;ap_uint<3> y=0;
    ap_int<48> acc[16];
#pragma HLS ARRAY_PARTITION variable=acc complete
    FLAT_MAC:for(int index=0;index<total;++index) {
#pragma HLS PIPELINE II=1
        int ix=(ap_uint<8>(x)*ap_uint<2>(sx)).to_int()+kx.to_int()-px;
        int cy=(ap_uint<3>(y)*ap_uint<2>(sy)).to_int()+ky.to_int();
        bool inside=ix>=0 && ix<iw;
        ap_int<16> scalar=0;
        if(!dw && inside)scalar=cache[cache_address(cy,ix,ic.to_uint()/16,iw,groups)][ic.to_uint()%16];
        AccBlock packet;
#pragma HLS ARRAY_PARTITION variable=packet.values complete
        for(int lane=0;lane<16;++lane) {
#pragma HLS UNROLL
            ap_int<16> sample=scalar;
            if(dw)sample=inside?cache[cache_address(cy,ix,cb/16,iw,groups)][lane]:ap_int<16>(0);
            ap_int<32> product=sample*weights[k.to_uint()][lane];
#pragma HLS BIND_OP variable=product op=mul impl=dsp latency=2
            ap_int<48> base=k==0?biases[lane]:acc[lane];
            ap_int<48> updated=base+product;
#pragma HLS BIND_OP variable=updated op=add impl=fabric latency=1
            acc[lane]=updated;packet.values[lane]=updated;
        }
        if(k==last_k) {
            packets.write(packet);k=0;ic=0;kx=0;ky=0;
            if(x==last_x){x=0;++y;}else ++x;
        } else {
            ++k;
            if(dw || ic==last_ic) {
                ic=0;
                if(kx==kw-1){kx=0;++ky;}else ++kx;
            } else ++ic;
        }
    }
}

static void consume_blocks(hls::stream<AccBlock>& packets,const signed char shifts[16],
    ap_int<16> output_cache[32768],int rows,int ow,int co,int cb,int n,int relu,int rs,int limit) {
#pragma HLS INLINE off
#pragma HLS ARRAY_PARTITION variable=shifts complete
#pragma HLS ARRAY_PARTITION variable=output_cache cyclic factor=8
    int pairs=(n+1)/2;
    ap_uint<10> pixels=ap_uint<3>(rows)*ap_uint<8>(ow);
    ap_uint<14> total=pixels*ap_uint<4>(pairs);
    ap_uint<4> pair=0,last_pair=pairs-1;ap_uint<10> pixel=0;
    AccBlock packet;
#pragma HLS ARRAY_PARTITION variable=packet.values complete
    FLAT_QUANTIZE:for(int index=0;index<total;++index) {
#pragma HLS PIPELINE II=1
        if(pair==0)packet=packets.read();
        for(int j=0;j<2;++j) {
#pragma HLS UNROLL
            int lane=pair.to_uint()*2+j;
            if(lane<n) {
                ap_uint<20> address=pixel*ap_uint<10>(co)+ap_uint<10>(cb+lane);
                output_cache[address.to_uint()]=finish(packet.values[lane],shifts[lane],relu,rs,limit);
            }
        }
        if(pair==last_pair){pair=0;++pixel;}else ++pair;
    }
}

static void compute_and_store(const ap_int<16> cache[4096][16],const ap_int<16> weights[1024][16],
    const ap_int<48> biases[16],const signed char shifts[16],ap_int<16> output_cache[32768],
    int rows,int ow,int co,int cb,int n,int iw,int ci,int groups,int kh,int kw,int sy,int sx,int px,int dw,int relu,int rs,int limit) {
#pragma HLS INLINE off
#pragma HLS DATAFLOW
#pragma HLS ARRAY_PARTITION variable=cache complete dim=2
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS ARRAY_PARTITION variable=biases complete
#pragma HLS ARRAY_PARTITION variable=shifts complete
#pragma HLS ARRAY_PARTITION variable=output_cache cyclic factor=8
    hls::stream<AccBlock> packets;
#pragma HLS STREAM variable=packets depth=4
    produce_blocks(cache,weights,biases,packets,rows,ow,iw,ci,groups,kh,kw,sy,sx,px,dw,cb);
    consume_blocks(packets,shifts,output_cache,rows,ow,co,cb,n,relu,rs,limit);
}
