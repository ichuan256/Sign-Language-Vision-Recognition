#include "kp_gemm_tile.hpp"
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdlib>

int main() {
    std::ifstream input("vectors.txt");
    int cases;
    if (!(input >> cases)) return 1;
    long long checked=0, max_error=0;
    for (int test=0; test<cases; ++test) {
        int m,n,k;
        input >> m >> n >> k;
        // Co-simulation adapters transfer declared AXI depths, not just the active tile.
        std::vector<ap_int<16>> a(65536),b(16384),output(1024);
        ap_int<64> bias[16];
        ap_int<8> shifts[16];
        long long value;
        for (int i=0;i<m*k;++i) { input>>value; a[i]=value; }
        for (int i=0;i<k*16;++i) { input>>value; b[i]=value; }
        for (auto& x:bias) { input>>value; x=value; }
        for (auto& x:shifts) { input>>value; x=value; }
        if (kp_gemm_tile(a.data(),b.data(),bias,shifts,output.data(),m,n,k)!=0) return 2;
        for (int i=0;i<m*n;++i) {
            auto x=output[i];
            input >> value;
            long long error=std::llabs(x.to_int64()-value);
            if (error>max_error) max_error=error;
            if (error) {
                std::cerr<<"MISMATCH case="<<test<<" actual="<<x<<" expected="<<value<<std::endl;
                return 3;
            }
            ++checked;
        }
    }
    std::vector<ap_int<16>> a(65536),b(16384),sentinel(1024);
    ap_int<64> bias[16] = {};
    ap_int<8> shifts[16] = {};
    sentinel[0]=321;
    if (kp_gemm_tile(a.data(),b.data(),bias,shifts,sentinel.data(),65,1,1)!=1 || sentinel[0]!=321) return 4;
    std::cout<<"CASES="<<cases<<" MATCHED="<<checked<<" MAX_LSB_ERROR="<<max_error<<std::endl;
    return input.good() ? 0 : 5;
}
