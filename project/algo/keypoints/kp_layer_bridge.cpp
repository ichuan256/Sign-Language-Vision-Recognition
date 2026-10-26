#include "kp_layer.hpp"
extern "C" __declspec(dllexport) int kp_layer_host(const short* a,const short* b,
    const long long* bias,const signed char* shift,short* out,const int* config) {
    return kp_layer(a,b,bias,shift,out,config);
}
