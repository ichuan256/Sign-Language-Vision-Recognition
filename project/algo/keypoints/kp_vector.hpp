#pragma once
enum { KP_ADD=0, KP_RELU=1, KP_MAX=2, KP_MEAN49=3, KP_SIGMOID=4, KP_SCALE=5 };
int kp_vector(const short* a,const short* b,short* out,
              int count,int operation,int shift,int alpha,int beta,int limit,int kernel);
