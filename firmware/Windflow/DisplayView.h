#pragma once
#include "Control.h"
namespace wf {
// Displayed dial phase is relative to boot: the incremental encoder has no absolute-angle sensor.
// Quantize telemetry once per frame so all transported strips show one coherent state.
struct DisplayFrame {
 State state=State::WaitPower;
 Fault fault=Fault::None;
 RotaryMode mode=RotaryMode::Normal;
 uint16_t dialDegrees=0,entryDegreesLeft=360,entryDetents=0,normalDetentsLeft=0;
 uint16_t normalPercent=0,boostPercent=0,nozzlePercent=100,pwmPercent=0;
 uint16_t rpm=0;
 int16_t temperatureTenths=0,pressureTenths=0,busTenths=0;
 bool on=false,night=false,entryReady=false,outletReady=false,powerReady=false,limited=false,thermal=false;
 bool temperaturesValid=false,pressureValid=false,pdReady=false;
 bool operator==(const DisplayFrame& b)const;
};
DisplayFrame displayFrame(const Control& c,const Inputs& in);
const char* displayFaultName(Fault f);
const char* displaySystemName(const DisplayFrame& f);
const char* displayEntryInstruction(const DisplayFrame& f);
}
