#include "kp_vector.hpp"
#include <vector>
#include <fstream>
#include <iostream>
int main() {
    std::ifstream input("vector_cases.txt");
    int tests;
    if (!(input>>tests)) return 1;
    long long matched=0;
    for (int test=0;test<tests;++test) {
        int n,op,shift,alpha,beta,limit,kernel,length;
        input>>n>>op>>shift>>alpha>>beta>>limit>>kernel>>length;
        std::vector<short> a(262144),b(4096),out(4096);
        int value;
        for (int i=0;i<length;++i) {input>>value;a[i]=value;}
        for (int i=0;i<n;++i) {input>>value;b[i]=value;}
        if (kp_vector(a.data(),b.data(),out.data(),n,op,shift,alpha,beta,limit,kernel)) return 2;
        for (int i=0;i<n;++i) {
            input>>value;
            if (out[i]!=value) {
                std::cerr<<"MISMATCH case="<<test<<" index="<<i<<" actual="<<out[i]<<" expected="<<value<<std::endl;
                return 3;
            }
            ++matched;
        }
    }
    std::cout<<"VECTOR_CASES="<<tests<<" MATCHED="<<matched<<" MAX_LSB_ERROR=0"<<std::endl;
    return input.good()?0:4;
}
