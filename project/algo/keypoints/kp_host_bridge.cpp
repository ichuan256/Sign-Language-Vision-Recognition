#include "kp_gemm_tile.hpp"
#include "kp_vector.hpp"
#include <cstdint>
static_assert(sizeof(ap_int<16>)==2,"16-bit host ABI mismatch");
static_assert(sizeof(ap_int<64>)==8,"64-bit host ABI mismatch");
static_assert(sizeof(ap_int<8>)==1,"8-bit host ABI mismatch");
extern "C" __declspec(dllexport)
int kp_gemm_host(const int16_t* a,const int16_t* b,const int64_t* bias,const int8_t* shift,
                 int16_t* out,int m,int n,int k) {
    return kp_gemm_tile(reinterpret_cast<const ap_int<16>*>(a),reinterpret_cast<const ap_int<16>*>(b),
        reinterpret_cast<const ap_int<64>*>(bias),reinterpret_cast<const ap_int<8>*>(shift),
        reinterpret_cast<ap_int<16>*>(out),m,n,k);
}
extern "C" __declspec(dllexport)
int kp_vector_host(const int16_t* a,const int16_t* b,int16_t* out,
                   int count,int op,int shift,int alpha,int beta,int limit,int kernel) {
    return kp_vector(a,b,out,count,op,shift,alpha,beta,limit,kernel);
}
