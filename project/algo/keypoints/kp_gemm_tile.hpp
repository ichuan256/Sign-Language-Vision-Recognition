#pragma once
#include <ap_int.h>

// Layer-engine building block only, NOT a complete hand-landmark network.
// A: rows x depth, B: depth x 16 (padded output columns).
// Bias uses per-column accumulator scale; shift = F_input + F_weight - F_output.
int kp_gemm_tile(const ap_int<16>* a, const ap_int<16>* b,
                 const ap_int<64>* bias, const ap_int<8>* shift,
                 ap_int<16>* out, int rows, int columns, int depth);
