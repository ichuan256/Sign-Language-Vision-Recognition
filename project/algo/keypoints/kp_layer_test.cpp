#include "kp_layer.hpp"
#include <fstream>
#include <iostream>
#include <vector>
int main() {
    std::ifstream f("layer_cases.txt");int cases;f>>cases;int outputs=0;
    for (int t=0;t<cases;++t) {
        int cfg[16];for (int i=0;i<16;++i) f>>cfg[i];
        int na=cfg[0]*cfg[1]*cfg[2],nb=cfg[6]*cfg[7]*cfg[5]*(cfg[12]?1:cfg[2]);
        int no=cfg[3]*cfg[4]*cfg[5];
        // The co-sim adapter snapshots declared AXI depths, including unused tails.
        std::vector<short>a(802816),b(451584),out(802816),gold(no);
        std::vector<long long>bias(672);std::vector<signed char>shift(672);
        int v;
        for(int i=0;i<na;++i)f>>a[i];for(int i=0;i<nb;++i)f>>b[i];
        for(int i=0;i<cfg[5];++i)f>>bias[i];
        for(int i=0;i<cfg[5];++i){f>>v;shift[i]=v;}
        for(int i=0;i<no;++i)f>>gold[i];
        if(!f || kp_layer(a.data(),b.data(),bias.data(),shift.data(),out.data(),cfg))return 1;
        for(int i=0;i<no;++i)if(out[i]!=gold[i]){
            std::cerr<<"Mismatch case="<<t<<" index="<<i<<" actual="<<out[i]<<" expected="<<gold[i]<<std::endl;return 2;
        }
        outputs+=no;
    }
    std::cout<<"LAYER_EXACT cases="<<cases<<" outputs="<<outputs<<" max_LSB=0"<<std::endl;
    return 0;
}
