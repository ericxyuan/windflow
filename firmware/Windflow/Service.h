#pragma once
#include "Control.h"
#include "Hardware.h"
#include "Lighting.h"
#include "Storage.h"
namespace wf {
class Service {
 char line_[128]{};size_t length_=0;bool overflow_=false;uint32_t telemetryAt_=0;
 void command(char* line,uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage);
public:
 void poll(uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage);
};
}
