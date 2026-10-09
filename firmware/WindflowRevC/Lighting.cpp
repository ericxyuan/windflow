#include "Lighting.h"
namespace wf {
void Lighting::begin(){ambient_.begin();ambient_.clear();display_.begin();}
bool Lighting::test(int i,int r,int g,int b,uint32_t now){
 if(i<0||i>=kAmbientCapacity||r<0||r>80||g<0||g>80||b<0||b>80)return false;
 testIndex_=i;testR_=r;testG_=g;testB_=b;testEnd_=now+2000;return true;
}
void Lighting::poll(uint32_t now,const Control& c,const Inputs& in){
 // The display is on the unswitched logic rail and remains available when ambient is disabled.
 display_.poll(now,c,in);
 if(now-at_<33)return;at_=now;
 if(!c.out.ledEnable){ambient_.clear();digitalWrite(pin::ambientLed,LOW);wasPowered_=false;return;}
 if(!wasPowered_){poweredAt_=now;wasPowered_=true;}if(now-poweredAt_<50)return;
 ambient_.clear();const Settings& s=c.settings;
 uint8_t a=s.night?s.nightAmbient:s.ambientBrightness;
 for(int i=0;i<s.ambientCount;i++)ambient_.setPixelColor(i,ambient_.Color(a,a*2/3,a/3));
 if(c.state==State::Service&&testIndex_>=0&&int32_t(testEnd_-now)>0){ambient_.clear();ambient_.setPixelColor(testIndex_,testR_,testG_,testB_);}
 ambient_.show();
}
}
