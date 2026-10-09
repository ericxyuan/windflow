#pragma once
#include <stdint.h>
namespace wf {
// Four valid quadrature transitions make one detent on PEC11H-S0024.
// Contact bounce reverses/cancels partial travel; a two-bit transition is an
// invalid observation, so discard its partial cycle instead of inventing motion.
class EncoderDecoder {
 uint8_t previous_=3;
 int8_t quarters_=0;
public:
 void reset(uint8_t state){previous_=state&3;quarters_=0;}
 int8_t transition(uint8_t state){
  static constexpr int8_t direction[]={0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0};
  state&=3;
  if((state^previous_)==3)quarters_=0;
  else quarters_+=direction[(previous_<<2)|state];
  previous_=state;
  if(quarters_>=4){quarters_=0;return 1;}
  if(quarters_<=-4){quarters_=0;return -1;}
  return 0;
 }
};
// The main loop atomically drains this count. Saturate a pathological backlog
// rather than wrapping its sign; normal input cannot reach these bounds.
inline int32_t accumulateEncoderDetent(int32_t count,int8_t detent){
 if(detent>0&&count<INT32_MAX)return count+1;
 if(detent<0&&count>INT32_MIN)return count-1;
 return count;
}
}
