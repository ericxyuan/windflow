#include "Display.h"
#include <hardware/pwm.h>
#include <hardware/clocks.h>
namespace wf {
void ScreenTransport::prepareLandscape(){
 // init() contains blocking delays. We perform the same controller setup below with timers.
 begin(kScreenSpiHz);
 _width=kScreenWidth;_height=kScreenHeight;rotation=3;
 _xstart=0;_ystart=0;_colstart=0;_rowstart=0;
}
void Display::begin(){
 for(uint8_t p:{pin::screenCs,pin::screenDc,pin::screenRst,pin::screenMosi,pin::screenSck}){pinMode(p,OUTPUT);digitalWrite(p,LOW);}
 // GP16 is slice0 channel A. GPIO0 is still an input, not routed to PWM.
 // Never use analogWriteFreq: fan GPIO6 and servo GPIO8 own separate fixed-frequency slices.
 gpio_set_function(pin::screenBacklight,GPIO_FUNC_PWM);
 pwm_config config=pwm_get_default_config();pwm_config_set_wrap(&config,255);
 pwm_config_set_clkdiv(&config,clock_get_hz(clk_sys)/(2000.f*256));
 pwm_init(pwm_gpio_to_slice_num(pin::screenBacklight),&config,true);
 backlightReady_=true;backlight(0);
}
void Display::backlight(uint8_t b){if(backlightReady_)pwm_set_gpio_level(pin::screenBacklight,b);}
void Display::stop(){
 backlight(0);
 if(init_!=Init::Off)SPI.end();
 for(uint8_t p:{pin::screenCs,pin::screenDc,pin::screenRst,pin::screenMosi,pin::screenSck}){pinMode(p,OUTPUT);digitalWrite(p,LOW);}
 init_=Init::Off;stableAt_=0;drawing_=false;haveFrame_=false;
}
bool Display::initialize(uint32_t now,const Inputs& in){
 // Do not talk to or illuminate an unpowered panel. PD need not be valid for a fault/status screen.
 if(!strip_.getBuffer()||!isfinite(in.logicV)||in.logicV<4.65f||in.logicV>5.35f){stop();return false;}
 if(init_==Init::Ready)return true;
 if(init_==Init::Off){
  if(!stableAt_){stableAt_=now;return false;}if(now-stableAt_<100)return false;
  // The TFT is write-only. Default SPI0 RX=GP16 would steal the backlight PWM pin.
  SPI.setRX(NOPIN);SPI.setTX(pin::screenMosi);SPI.setSCK(pin::screenSck);
  screen_.prepareLandscape();digitalWrite(pin::screenRst,LOW);init_=Init::ResetLow;initAt_=now;return false;
 }
 if(init_==Init::ResetLow&&now-initAt_>=20){digitalWrite(pin::screenRst,HIGH);init_=Init::ResetHigh;initAt_=now;}
 else if(init_==Init::ResetHigh&&now-initAt_>=150){screen_.sendCommand(ST77XX_SWRESET);init_=Init::SoftwareReset;initAt_=now;}
 else if(init_==Init::SoftwareReset&&now-initAt_>=150){screen_.sendCommand(ST77XX_SLPOUT);init_=Init::SleepOut;initAt_=now;}
 else if(init_==Init::SleepOut&&now-initAt_>=120){
  const uint8_t format=0x55,orientation=ST77XX_MADCTL_MX|ST77XX_MADCTL_MV|ST77XX_MADCTL_RGB;
  screen_.sendCommand(ST77XX_COLMOD,&format,1);screen_.sendCommand(ST77XX_MADCTL,&orientation,1);
  screen_.sendCommand(ST77XX_INVON);screen_.sendCommand(ST77XX_NORON);init_=Init::Normal;initAt_=now;
 }
 else if(init_==Init::Normal&&now-initAt_>=10){screen_.sendCommand(ST77XX_DISPON);init_=Init::On;initAt_=now;}
 else if(init_==Init::On&&now-initAt_>=20){init_=Init::Ready;haveFrame_=false;return true;}
 return false;
}
bool Display::test(uint8_t pattern,uint32_t now){if(pattern<1||pattern>5)return false;testPattern_=pattern;testEnd_=now+2000;return true;}
void Display::poll(uint32_t now,const Control& c,const Inputs& in){
 if(!initialize(now,in))return;
 bool fault=c.state==State::Fault;
 uint8_t brightness=fault?36:c.settings.night?c.settings.nightMain:c.settings.mainBrightness;
 // Thermal protection disables ambient lighting, but keeps the system warning readable.
 if(c.out.thermal&&brightness<16)brightness=16;
 uint8_t pattern=!fault&&c.state==State::Service&&testPattern_&&int32_t(testEnd_-now)>0?testPattern_:0;
 if(c.state==State::Service&&brightness<36)brightness=36; // Explicit service mode must remain legible.
 bool urgent=fault&&(frame_.state!=c.state||frame_.fault!=c.fault);
 if(urgent){drawing_=false;haveFrame_=false;}
 if(!drawing_){
  if(haveFrame_&&now-lastFrame_<kScreenRefreshMs)return;
  DisplayFrame next=displayFrame(c,in);lastFrame_=now;
  if(haveFrame_&&next==frame_&&pattern==paintPattern_){backlight(brightness);return;}
  frame_=next;paintPattern_=pattern;stripe_=0;drawing_=true;
 }else if(now-lastSlice_<kScreenSliceMs)return;
 int16_t y=stripe_*kScreenRenderRows,h=kScreenHeight-y;if(h>kScreenRenderRows)h=kScreenRenderRows;
 renderDisplay(strip_,frame_,y,paintPattern_);
 // One contiguous 320x16 transfer is 3.41ms of raw SPI wire time at 24MHz.
 // Sensor/control polling resumes between strips; hardware PWM and tach IRQ continue throughout.
 screen_.startWrite();screen_.setAddrWindow(0,y,kScreenWidth,h);
 screen_.writePixels(strip_.getBuffer(),uint32_t(kScreenWidth)*h);screen_.endWrite();
 lastSlice_=now;stripe_++;
 if(stripe_==(kScreenHeight+kScreenRenderRows-1)/kScreenRenderRows){drawing_=false;haveFrame_=true;}
 // Hide uninitialized GRAM until all 15 initial strips have been painted.
 if(haveFrame_)backlight(brightness);
}
}
