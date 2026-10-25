#pragma once
// config: IH IW CI OH OW CO KH KW SY SX PY PX DW RELU RELU_SHIFT LIMIT
int kp_layer(const short* a,const short* b,const long long* bias,
             const signed char* shift,short* out,const int* config);
