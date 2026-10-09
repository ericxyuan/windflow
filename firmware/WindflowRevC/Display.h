#pragma once
#include "DisplayLayout.h"
#include <Adafruit_ST7789.h>
#include <SPI.h>
namespace wf {
class ScreenTransport:public Adafruit_ST7789 {
public:
 ScreenTransport():Adafruit_ST7789(&SPI,pin::screenCs,pin::screenDc,-1){}
 void prepareLandscape();
};
class Display {
 ScreenTransport screen_;
 GFXcanvas16 strip_{kScreenWidth,kScreenRenderRows}; // 10,240 bytes; no full-frame allocation.
 DisplayFrame frame_{};
 enum class Init:uint8_t {Off,ResetLow,ResetHigh,SoftwareReset,SleepOut,Normal,On,Ready};
 Init init_=Init::Off;
 uint32_t initAt_=0,stableAt_=0,lastFrame_=0,lastSlice_=0,testEnd_=0;
 uint8_t stripe_=0,testPattern_=0,paintPattern_=0;
 bool drawing_=false,haveFrame_=false,backlightReady_=false;
 void backlight(uint8_t brightness);
 void stop();
 bool initialize(uint32_t now,const Inputs& in);
public:
 void begin();
 void poll(uint32_t now,const Control& c,const Inputs& in);
 bool test(uint8_t pattern,uint32_t now);
 bool ready()const{return init_==Init::Ready&&haveFrame_;}
};
}
