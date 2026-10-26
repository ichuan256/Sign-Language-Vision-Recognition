#pragma once
#include <ap_int.h>
static short rounded(long long value,int shift) {
    bool neg=value<0;
    unsigned long long m=neg ? -value : value;
    if (shift<0) {
        int left=-shift;
        if (m>((neg ? 32768ULL : 32767ULL)>>left)) return neg ? -32768 : 32767;
        m <<= left;
    } else if (shift>0) {
        unsigned long long q=m>>shift,r=m&((1ULL<<shift)-1),half=1ULL<<(shift-1);
        if (r>half || (r==half && (q&1))) ++q;
        m=q;
    }
    long long result=neg ? -static_cast<long long>(m) : static_cast<long long>(m);
    return result>32767 ? 32767 : result<-32768 ? -32768 : short(result);
}
static short finish(ap_int<48> sum,int shift,int relu,int relu_shift,int limit) {
    short value=rounded(sum.to_int64(),shift);
    if (relu) {
        if (value<0) value=0;
        if (limit>=0 && value>limit) value=short(limit);
        value=rounded(value,relu_shift);
    }
    return value;
}
