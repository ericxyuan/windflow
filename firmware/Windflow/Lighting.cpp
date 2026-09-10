#include "Lighting.h"
namespace wf {
void Lighting::begin(){main_.begin();ambient_.begin();for(uint8_t p:{pin::statusR,pin::statusG,pin::statusB}){pinMode(p,OUTPUT);digitalWrite(p,LOW);}main_.clear();ambient_.clear();}
bool Lighting::test(int i,int r,int g,int b,uint32_t now){if(i<0||i>=kMainCapacity+kAmbientCapacity||r<0||r>80||g<0||g>80||b<0||b>80)return false;testIndex_=i;testR_=r;testG_=g;testB_=b;testEnd_=now+2000;return true;}
void Lighting::poll(uint32_t now,const Control& c){
 if(now-at_<33)return;at_=now;
 bool fault=c.state==State::Fault,waiting=c.state==State::WaitPower,setup=c.state==State::Uncommissioned||c.state==State::Service;
 bool flash=(now%1200)<150;
 // These three discrete LEDs remain powered when cosmetic lighting is disconnected.
 digitalWrite(pin::statusR,(fault&&flash)||(!fault&&c.out.thermal));
 digitalWrite(pin::statusG,!fault&&!waiting&&!setup&&(!c.settings.night||flash));
 digitalWrite(pin::statusB,(waiting||setup||c.out.boostLimited)&&flash);
 if(!c.out.ledEnable){main_.clear();ambient_.clear();digitalWrite(pin::mainLed,LOW);digitalWrite(pin::ambientLed,LOW);wasPowered_=false;return;}
 if(!wasPowered_){poweredAt_=now;wasPowered_=true;}if(now-poweredAt_<50)return;
 main_.clear();ambient_.clear();const Settings& s=c.settings;
 uint8_t b=s.night?s.nightMain:s.mainBrightness,a=s.night?s.nightAmbient:s.ambientBrightness;
 bool animation=!s.night&&(c.state==State::RampUp||c.state==State::RampDown);
 float level=animation?c.out.animation:(s.on?s.setting/1000.f:0);
 bool boost=!animation&&s.on&&s.setting/1000.f>s.boostThreshold;
 int boundary=int(lroundf(s.mainCount*s.boostThreshold));
 for(int i=0;i<s.mainCount;i++){
  float fill=clamp(level*s.mainCount-i,0,1);
  uint8_t v=(uint8_t)(b*fill);
  main_.setPixelColor(i,boost?main_.Color(v,0,v/3):main_.Color(0,v*2/3,v));
  if(!animation&&i==boundary&&fill<.01f&&s.on&&!s.night)main_.setPixelColor(i,main_.Color(3,1,0));
 }
 for(int i=0;i<s.ambientCount;i++)ambient_.setPixelColor(i,ambient_.Color(a,a*2/3,a/3));
 if(c.out.boostLimited&&!s.night&&flash)main_.setPixelColor(0,main_.Color(12,4,0));
 if(c.state==State::Service&&testIndex_>=0&&int32_t(testEnd_-now)>0){main_.clear();ambient_.clear();
  if(testIndex_<kMainCapacity)main_.setPixelColor(testIndex_,testR_,testG_,testB_);
  else ambient_.setPixelColor(testIndex_-kMainCapacity,testR_,testG_,testB_);
 }
 main_.show();ambient_.show();
}
}
