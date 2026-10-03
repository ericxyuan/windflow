#pragma once
#include <Adafruit_NeoPixel.h>
#include "Display.h"
namespace wf {
class Lighting{
 Adafruit_NeoPixel ambient_{kAmbientCapacity,pin::ambientLed,NEO_GRB+NEO_KHZ800};
 Display display_;
 uint32_t at_=0,poweredAt_=0;bool wasPowered_=false;
 int testIndex_=-1;uint8_t testR_=0,testG_=0,testB_=0;uint32_t testEnd_=0;
public:
 void begin();
 void poll(uint32_t now,const Control& c,const Inputs& in);
 bool test(int index,int r,int g,int b,uint32_t now);
 bool screenTest(uint8_t pattern,uint32_t now){return display_.test(pattern,now);}
 bool displayReady()const{return display_.ready();}
};
}
