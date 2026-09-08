#pragma once
#include "Control.h"
namespace wf {
class Hardware {
public:
 Inputs in{};
 void begin();
 void poll(uint32_t now,const Settings& s);
 void apply(const Outputs& o);
private:
 uint32_t lastFast_=0,lastTemp_=0,lastPressure_=0,lastPd_=0;
 uint32_t goodTemp_=0,goodPressure_=0,goodPd_=0,pressureStart_=0;
 uint8_t pressureState_=0;
};
}
