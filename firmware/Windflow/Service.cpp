#include "Service.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
namespace wf {
static bool number(const char* v,float& f){if(!v)return false;char* end;f=strtof(v,&end);return *v&&!*end&&isfinite(f);}
static void reply(const char* s){if(Serial.availableForWrite()>int(strlen(s)+2))Serial.println(s);}
struct Field{const char* name;size_t offset;uint8_t kind;bool cosmetic;};
#define WF_FLOAT_FIELD(name) {#name,offsetof(Settings,name),0,false}
#define WF_BYTE_FIELD(name) {#name,offsetof(Settings,name),1,false}
#define WF_COSMETIC_FIELD(name) {#name,offsetof(Settings,name),1,true}
static const Field fields[]={WF_FLOAT_FIELD(boostThreshold),WF_FLOAT_FIELD(minAreaRatio),WF_FLOAT_FIELD(minPwm),WF_FLOAT_FIELD(maxPwm),WF_FLOAT_FIELD(rpmAtMax),WF_FLOAT_FIELD(pressureSoft),WF_FLOAT_FIELD(pressureHard),WF_FLOAT_FIELD(warnC),WF_FLOAT_FIELD(tripC),WF_FLOAT_FIELD(busScale),WF_FLOAT_FIELD(logicScale),WF_BYTE_FIELD(encoderReverse),WF_BYTE_FIELD(ambientCount),WF_COSMETIC_FIELD(mainBrightness),WF_COSMETIC_FIELD(ambientBrightness),WF_COSMETIC_FIELD(nightMain),WF_COSMETIC_FIELD(nightAmbient)};
void Service::command(char* line,uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage){
 char* cmd=strtok(line," ");if(!cmd)return;
 if(!strcmp(cmd,"status")){
  char b[320];snprintf(b,sizeof(b),"state=%u fault=%u u=%u mode=%u entry=%u left=%u dial=%u pwm=%.3f close=%.3f rpm=%.0f dp=%.2f temp=%.1f/%.1f bus=%.2f logic=%.2f servo=%u adc=%u pd=%u tempOK=%u dpOK=%u guard=%u commissioned=%u fs=%u\n",unsigned(c.state),unsigned(c.fault),c.settings.setting,unsigned(c.rotaryMode()),c.entryDetents(),c.entryDetentsRemaining(),c.encoderPositionDetents(),c.out.pwm,c.out.closure,hw.in.rpm,hw.in.pressurePa,hw.in.tempPower,hw.in.tempMotor,hw.in.busV,hw.in.logicV,c.out.servoUs,hw.in.servoAdc,hw.in.pd15v,hw.in.tempsValid,hw.in.pressureValid,hw.in.guardClosed,c.settings.commissioned,storage.available());
  if(Serial.availableForWrite()>=int(strlen(b)))Serial.print(b);return;
 }
 if(!strcmp(cmd,"ack")){reply(c.acknowledge(now,hw.in)?"OK fault acknowledged; fan off":"ERR unsafe to acknowledge");return;}
 if(!strcmp(cmd,"help")){reply("status ack; service: evidence, set KEY VALUE, fan 0..100, jog -10..10, capture 0..4, zero, measure fan-min|fan-max, led 0..7 R G B (ambient), screen 1..5 (R/G/B/white/grid), format ERASE, commit MEASURED, exit");return;}
 if(c.state!=State::Service){reply("ERR fit service jumper and hold encoder during boot for 4s");return;}
 if(!strcmp(cmd,"evidence")){char b[96];snprintf(b,sizeof(b),"captures=0x%02x zero=%u fanMin=%u fanMax=%u",calibration_.captures,calibration_.zeroed,calibration_.fanMin,calibration_.fanMax);reply(b);return;}
 if(!strcmp(cmd,"exit")){c.exitService(now);reply("OK");return;}
 if(!strcmp(cmd,"set")){
  char* key=strtok(nullptr," ");float value;
  if(!key||!number(strtok(nullptr," "),value)||strtok(nullptr," ")){reply("ERR syntax");return;}
  Settings proposed=c.settings;bool found=false,cosmetic=false;
  for(const Field& f:fields)if(!strcmp(key,f.name)){
   if(f.kind){if(value<0||value>255||floorf(value)!=value){reply("ERR integer required");return;}*(uint8_t*)((uint8_t*)&proposed+f.offset)=uint8_t(value);}
   else *(float*)((uint8_t*)&proposed+f.offset)=value;found=true;cosmetic=f.cosmetic;break;
  }
  if(!found||!valid(proposed)){reply("ERR unknown key or unsafe value");return;}
  // Backlight/ambient brightness cannot alter the calibrated fan, nozzle or
  // sensor mapping. Keep both persisted commissioning and session evidence.
  // Everything else still invalidates evidence, including encoder direction
  // and the physical LED count. All fields use the same bounded validation.
  if(!cosmetic){proposed.commissioned=0;calibration_.reset();}
  c.settings=proposed;c.markChanged(now);
  reply(cosmetic?"OK brightness updated; calibration retained":"OK evidence cleared; recommission required");return;
 }
 if(!strcmp(cmd,"fan")){float v;bool ok=number(strtok(nullptr," "),v)&&!strtok(nullptr," ")&&v>=0&&v<=100&&(v==0||((calibration_.captures&1)&&abs(int(hw.in.servoAdc)-int(c.settings.feedback[0]))<60))&&c.testFan(v/100,now);reply(ok?"OK fan test expires in 10s; zero stops both loads":"ERR range or panels not calibrated/open");return;}
 if(!strcmp(cmd,"jog")){float v;bool ok=number(strtok(nullptr," "),v)&&!strtok(nullptr," ")&&floorf(v)==v&&v>=-10&&v<=10&&c.jogServo(int(v),now);reply(ok?"OK servo powered for 0.8s":"ERR max 10us per jog");return;}
 if(!strcmp(cmd,"capture")){
  float v;if(!number(strtok(nullptr," "),v)||strtok(nullptr," ")||v<0||v>4||floorf(v)!=v||!calibration_.capture(int(v),c.settings,c.out,hw.in)){reply("ERR jog; measure angle; wait 0.3s for stable feedback; capture before timeout");return;}
  c.markChanged(now);reply("OK captured pulse/feedback; all five points required");return;
 }
 if(!strcmp(cmd,"zero")){
  if(strtok(nullptr," ")||!calibration_.zero(c.settings)){reply("ERR stop both loads; wait for stable pressure within 2Pa for 1s");return;}
  c.markChanged(now);reply("OK pressure zero recorded");return;
 }
 if(!strcmp(cmd,"measure")){
  char* which=strtok(nullptr," ");bool maximum=which&&!strcmp(which,"fan-max");
  if(!which||(!maximum&&strcmp(which,"fan-min"))||strtok(nullptr," ")||!calibration_.measureFan(maximum,c.settings)){reply("ERR test exact min/max PWM for 5s with stable tach first");return;}
  c.markChanged(now);reply(maximum?"OK measured maximum RPM saved in RAM":"OK minimum PWM stability recorded");return;
 }
 if(!strcmp(cmd,"led")){
  float v[4];for(int i=0;i<4;i++)if(!number(strtok(nullptr," "),v[i])||floorf(v[i])!=v[i]){reply("ERR syntax");return;}
  reply(!strtok(nullptr," ")&&lights.test(int(v[0]),int(v[1]),int(v[2]),int(v[3]),now)?"OK":"ERR bounds");return;
 }
 if(!strcmp(cmd,"screen")){
  float v;bool ok=number(strtok(nullptr," "),v)&&!strtok(nullptr," ")&&floorf(v)==v&&v>=1&&v<=5&&lights.screenTest(uint8_t(v),now);
  reply(ok?"OK screen test expires in 2s":"ERR screen 1..5 (R/G/B/white/grid)");return;
 }
 if(!strcmp(cmd,"format")){
  char* yes=strtok(nullptr," ");if(!yes||strcmp(yes,"ERASE")||strtok(nullptr," ")||c.out.fanEnable||c.out.servoEnable){reply("ERR loads must be off; format ERASE");return;}
  reply(storage.format()?"OK blank settings filesystem":"ERR format");c.settings.commissioned=0;calibration_.reset();return;
 }
 if(!strcmp(cmd,"commit")){
  char* yes=strtok(nullptr," ");Settings proposed=c.settings;proposed.commissioned=1;
  // An already commissioned profile remains measured after cosmetic-only edits.
  // Any safety/mechanical set, capture, zero or RPM measurement clears that flag
  // and therefore still requires the complete current-session evidence chain.
  bool measured=c.settings.commissioned||calibration_.complete();
  if(!yes||strcmp(yes,"MEASURED")||strtok(nullptr," ")||!measured||!valid(proposed)||c.out.fanEnable||c.out.servoEnable||!hw.in.pd15v||!hw.in.tempsValid||!hw.in.pressureValid||!hw.in.guardClosed||!hw.in.fanPowerGood||!hw.in.servoPowerGood||!isfinite(hw.in.busV)||hw.in.busV<14.5f||hw.in.busV>16||!isfinite(hw.in.logicV)||hw.in.logicV<4.65f||hw.in.logicV>5.35f||!isfinite(hw.in.tempPower)||!isfinite(hw.in.tempMotor)||hw.in.tempPower>proposed.warnC-5||hw.in.tempMotor>proposed.warnC-5){reply("ERR require measured calibration; stop loads; check sensors");return;}
  if(storage.save(proposed)){c.settings=proposed;c.settingsDirty=false;reply("OK calibrated settings saved and verified");}else reply("ERR storage; format only on first commissioning");return;
 }
 reply("ERR command");
}
void Service::poll(uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage){
 bool active=c.state==State::Service;if(active&&!wasService_)calibration_.reset();wasService_=active;
 calibration_.observe(now,c,hw.in);
 // Bounded work per loop; a flooded USB console cannot starve safety.
 for(int n=0;n<24&&Serial.available();n++){
  char b=Serial.read();if(b=='\r')continue;
  if(b=='\n'){if(!overflow_){line_[length_]=0;command(line_,now,c,hw,lights,storage);}else reply("ERR line too long");length_=0;overflow_=false;}
  else if(length_<sizeof(line_)-1&&!overflow_)line_[length_++]=b;else overflow_=true;
 }
}
}
