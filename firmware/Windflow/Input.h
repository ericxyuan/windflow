#pragma once
#include <Arduino.h>
#include "Config.h"
namespace wf {
struct Events{int steps=0;bool shortPress=false,longPress=false;};
class Input{
 uint8_t previous_=3;int accum_=0;bool raw_=false,down_=false,longSent_=false;
 uint32_t edge_=0,pressed_=0;
public:
 void begin(){for(uint8_t p:{pin::encoderA,pin::encoderB,pin::button})pinMode(p,INPUT_PULLUP);previous_=(digitalRead(pin::encoderA)<<1)|digitalRead(pin::encoderB);}
 bool pressed()const{return down_;}
 Events poll(uint32_t now){
  Events e;static const int8_t q[]={0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0};
  uint8_t a=(digitalRead(pin::encoderA)<<1)|digitalRead(pin::encoderB);
  if((a^previous_)==3)accum_=0;else accum_+=q[(previous_<<2)|a];previous_=a;
  if(accum_>=4){e.steps=1;accum_=0;}if(accum_<=-4){e.steps=-1;accum_=0;}
  bool r=digitalRead(pin::button)==LOW;if(r!=raw_){raw_=r;edge_=now;}
  if(r!=down_&&now-edge_>=25){down_=r;if(down_){pressed_=now;longSent_=false;}else if(!longSent_&&now-pressed_>=40)e.shortPress=true;}
  if(down_&&!longSent_&&now-pressed_>=1200){e.longPress=true;longSent_=true;}
  return e;
 }
};
}
