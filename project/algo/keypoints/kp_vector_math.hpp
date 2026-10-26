#pragma once
static short saturated(long long value) {
    if(value>32767)return 32767;if(value<-32768)return -32768;return short(value);
}
static short scale(long long value,int shift) {
    bool negative=value<0;unsigned long long magnitude=negative?-value:value;
    if(shift<0) {
        int left=-shift;
        if(magnitude>((negative?32768ULL:32767ULL)>>left))return negative?-32768:32767;
        magnitude<<=left;
    } else if(shift>0) {
        unsigned long long q=magnitude>>shift,r=magnitude&((1ULL<<shift)-1),half=1ULL<<(shift-1);
        if(r>half || (r==half && (q&1)))++q;magnitude=q;
    }
    return saturated(negative?-static_cast<long long>(magnitude):static_cast<long long>(magnitude));
}
static short mean49(long long sum,int shift) {
    bool negative=sum<0;unsigned long long magnitude=negative?-sum:sum,denominator=49;
    if(shift<0)magnitude<<=-shift;else denominator<<=shift;
    unsigned long long q=magnitude/denominator,r=magnitude%denominator;
    if(r>denominator-r || (r==denominator-r && (q&1)))++q;
    return saturated(negative?-static_cast<long long>(q):static_cast<long long>(q));
}
