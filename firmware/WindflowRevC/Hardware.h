#pragma once
#include "Control.h"
#include "VescProtocol.h"
namespace wf {
class Hardware {
public:
 Inputs in{};
 void begin();
 void poll(uint32_t now,const Settings& s);
 void apply(const Outputs& o,const Settings& s,uint32_t now);
private:
 uint32_t lastFast_=0,lastTemp_=0,lastPressure_=0,lastPd_=0;
 uint32_t goodTemp_=0,goodPressure_=0,goodPd_=0,pressureStart_=0;
 uint8_t pressureState_=0;
 VescParser escParser_{};EscTelemetry esc_{};
 uint32_t lastEscCommand_=0,lastEscRequest_=0;
 bool escPowered_=false;
};
}
