#pragma once
#include <Adafruit_NeoPixel.h>
#include "Control.h"
namespace wf {
class Lighting{
 Adafruit_NeoPixel main_{kMainCapacity,pin::mainLed,NEO_GRB+NEO_KHZ800};
 Adafruit_NeoPixel ambient_{kAmbientCapacity,pin::ambientLed,NEO_GRB+NEO_KHZ800};
 uint32_t at_=0,poweredAt_=0;bool wasPowered_=false;
 int testIndex_=-1;uint8_t testR_=0,testG_=0,testB_=0;uint32_t testEnd_=0;
public:
 void begin();
 void poll(uint32_t now,const Control& c);
 bool test(int index,int r,int g,int b,uint32_t now);
};
}
