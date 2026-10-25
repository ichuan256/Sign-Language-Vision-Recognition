#include "kp_gemm_tile.hpp"

static ap_int<16> requantize(ap_int<48> value, int shift) {
    ap_int<96> wide = value;
    bool negative = wide < 0;
    ap_uint<96> magnitude = negative ? ap_uint<96>(-wide) : ap_uint<96>(wide);
    if (shift > 0) {
        ap_uint<96> quotient = magnitude >> shift;
        ap_uint<96> mask = (ap_uint<96>(1) << shift) - 1;
        ap_uint<96> remainder = magnitude & mask;
        ap_uint<96> half = ap_uint<96>(1) << (shift - 1);
        if (remainder > half || (remainder == half && quotient[0])) ++quotient;
        magnitude = quotient;
    } else if (shift < 0) {
        magnitude <<= -shift;
    }
    wide = ap_int<96>(magnitude);
    if (negative) wide = -wide;
    if (wide > 32767) return 32767;
    if (wide < -32768) return -32768;
    return ap_int<16>(wide);
}

int kp_gemm_tile(const ap_int<16>* a, const ap_int<16>* b,
                 const ap_int<64>* bias, const ap_int<8>* shift,
                 ap_int<16>* out, int rows, int columns, int depth) {
#pragma HLS INTERFACE m_axi port=a offset=slave bundle=activ depth=65536 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=b offset=slave bundle=weights depth=16384 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=bias offset=slave bundle=params depth=16
#pragma HLS INTERFACE m_axi port=shift offset=slave bundle=params depth=16
#pragma HLS INTERFACE m_axi port=out offset=slave bundle=output_data depth=1024 max_write_burst_length=64
#pragma HLS INTERFACE s_axilite port=a bundle=control
#pragma HLS INTERFACE s_axilite port=b bundle=control
#pragma HLS INTERFACE s_axilite port=bias bundle=control
#pragma HLS INTERFACE s_axilite port=shift bundle=control
#pragma HLS INTERFACE s_axilite port=out bundle=control
#pragma HLS INTERFACE s_axilite port=rows bundle=control
#pragma HLS INTERFACE s_axilite port=columns bundle=control
#pragma HLS INTERFACE s_axilite port=depth bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    if (rows < 1 || rows > 64 || columns < 1 || columns > 16 || depth < 1 || depth > 1024) return 1;
    ap_int<16> weights[1024][16];
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_2p impl=bram
    ap_int<48> biases[16];
    ap_int<8> shifts[16];
#pragma HLS ARRAY_PARTITION variable=biases complete
#pragma HLS ARRAY_PARTITION variable=shifts complete
    PARAMS: for (int c=0; c<16; ++c) {
#pragma HLS PIPELINE off
        if (c < columns) {
            if (bias[c] >= (ap_int<64>(1)<<47) || bias[c] < -(ap_int<64>(1)<<47)) return 3;
            biases[c] = bias[c];
            shifts[c] = shift[c];
            if (shifts[c] < -31 || shifts[c] > 47) return 2;
        } else {
            biases[c] = 0;
            shifts[c] = 0;
        }
    }
    LOAD_K: for (int k=0; k<depth; ++k) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=1024 avg=128
        LOAD_C: for (int c=0; c<16; ++c) {
#pragma HLS PIPELINE II=1
            weights[k][c] = b[k*16+c];
        }
    }
    ROWS: for (int r=0; r<rows; ++r) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=64 avg=32
        ap_int<48> acc[16];
#pragma HLS ARRAY_PARTITION variable=acc complete
        INIT: for (int c=0; c<16; ++c) {
#pragma HLS UNROLL
            acc[c] = biases[c];
        }
        MAC_K: for (int k=0; k<depth; ++k) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=1024 avg=128
#pragma HLS PIPELINE II=1
            ap_int<16> x = a[r*depth+k];
            MAC_C: for (int c=0; c<16; ++c) {
#pragma HLS UNROLL
                ap_int<32> product = x * weights[k][c];
                acc[c] += product;
            }
        }
        STORE: for (int c=0; c<columns; ++c) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=16 avg=16
#pragma HLS PIPELINE II=1
            out[r*columns+c] = requantize(acc[c], shifts[c]);
        }
    }
    return 0;
}
