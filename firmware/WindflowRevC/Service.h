#pragma once
#include "Control.h"
#include "Hardware.h"
#include "Lighting.h"
#include "Storage.h"
#include "Calibration.h"
namespace wf {
class Service {
 char line_[128]{};size_t length_=0;bool overflow_=false,wasService_=false;
 Calibration calibration_;
 void command(char* line,uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage);
public:
 void poll(uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage);
};
}
