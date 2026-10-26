#include "kp_layer.hpp"
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdint>
template<typename T> class AlignedBuffer {
    std::vector<T> storage;
    T* pointer;
public:
    explicit AlignedBuffer(std::size_t n):storage(n+64/sizeof(T)) {
        std::uintptr_t address=reinterpret_cast<std::uintptr_t>(storage.data());
        pointer=reinterpret_cast<T*>((address+63)&~std::uintptr_t(63));
    }
    T& operator[](std::size_t index){return pointer[index];}
    T* data(){return pointer;}
};
int main() {
    std::ifstream f("layer_cases.txt");int cases;f>>cases;int outputs=0;
    for (int t=0;t<cases;++t) {
        AlignedBuffer<int> cfg_buffer(16);int* cfg=cfg_buffer.data();
        for (int i=0;i<16;++i) f>>cfg[i];
        int na=cfg[0]*cfg[1]*cfg[2],nb=cfg[6]*cfg[7]*cfg[5]*(cfg[12]?1:cfg[2]);
        int no=cfg[3]*cfg[4]*cfg[5];
        // The co-sim adapter snapshots declared AXI depths, including unused tails.
        AlignedBuffer<short>a(802816),b(451584),out(802816);std::vector<short>gold(no);
        AlignedBuffer<long long>bias(672);AlignedBuffer<signed char>shift(672);
        int v;
        for(int i=0;i<na;++i)f>>a[i];for(int i=0;i<nb;++i)f>>b[i];
        for(int i=0;i<cfg[5];++i)f>>bias[i];
        for(int i=0;i<cfg[5];++i){f>>v;shift[i]=v;}
        for(int i=0;i<no;++i)f>>gold[i];
        for(int i=no;i<no+8 && i<802816;++i)out[i]=12345;
        if(!f || kp_layer(a.data(),b.data(),bias.data(),shift.data(),out.data(),cfg))return 1;
        for(int i=0;i<no;++i)if(out[i]!=gold[i]){
            std::cerr<<"Mismatch case="<<t<<" index="<<i<<" actual="<<out[i]<<" expected="<<gold[i]<<std::endl;return 2;
        }
        for(int i=no;i<no+8 && i<802816;++i)if(out[i]!=12345)return 3;
        outputs+=no;
    }
    std::cout<<"LAYER_EXACT cases="<<cases<<" outputs="<<outputs<<" max_LSB=0"<<std::endl;
    return 0;
}
