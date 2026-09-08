#include "Service.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
namespace wf {
static bool number(const char* v,float& f){if(!v)return false;char* end;f=strtof(v,&end);return *v&&!*end&&isfinite(f);}
static void reply(const char* s){if(Serial.availableForWrite()>int(strlen(s)+2))Serial.println(s);}
struct Field{const char* name;size_t offset;uint8_t kind;};
#define WF_FLOAT_FIELD(name) {#name,offsetof(Settings,name),0}
#define WF_BYTE_FIELD(name) {#name,offsetof(Settings,name),1}
static const Field fields[]={WF_FLOAT_FIELD(boostThreshold),WF_FLOAT_FIELD(minAreaRatio),WF_FLOAT_FIELD(minPwm),WF_FLOAT_FIELD(maxPwm),WF_FLOAT_FIELD(rpmAtMax),WF_FLOAT_FIELD(pressureSoft),WF_FLOAT_FIELD(pressureHard),WF_FLOAT_FIELD(warnC),WF_FLOAT_FIELD(tripC),WF_FLOAT_FIELD(busScale),WF_FLOAT_FIELD(logicScale),WF_BYTE_FIELD(encoderReverse),WF_BYTE_FIELD(mainCount),WF_BYTE_FIELD(ambientCount),WF_BYTE_FIELD(mainBrightness),WF_BYTE_FIELD(ambientBrightness),WF_BYTE_FIELD(nightMain),WF_BYTE_FIELD(nightAmbient)};
void Service::command(char* line,uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage){
 char* cmd=strtok(line," ");if(!cmd)return;
 if(!strcmp(cmd,"status")){
  char b[250];snprintf(b,sizeof(b),"state=%u fault=%u u=%u pwm=%.3f close=%.3f rpm=%.0f dp=%.2f temp=%.1f/%.1f bus=%.2f logic=%.2f servo=%u adc=%u pd=%u tempOK=%u dpOK=%u guard=%u commissioned=%u fs=%u\n",unsigned(c.state),unsigned(c.fault),c.settings.setting,c.out.pwm,c.out.closure,hw.in.rpm,hw.in.pressurePa,hw.in.tempPower,hw.in.tempMotor,hw.in.busV,hw.in.logicV,c.out.servoUs,hw.in.servoAdc,hw.in.pd15v,hw.in.tempsValid,hw.in.pressureValid,hw.in.guardClosed,c.settings.commissioned,storage.available());
  if(Serial.availableForWrite()>=int(strlen(b)))Serial.print(b);return;
 }
 if(!strcmp(cmd,"ack")){reply(c.acknowledge(now,hw.in)?"OK fault acknowledged; fan off":"ERR unsafe to acknowledge");return;}
 if(!strcmp(cmd,"help")){reply("status ack; service: set KEY VALUE, fan 0..100, jog -10..10, capture 0..4, zero, led 0..23 R G B, format ERASE, commit MEASURED, exit");return;}
 if(c.state!=State::Service){reply("ERR fit service jumper and hold encoder during boot for 4s");return;}
 if(!strcmp(cmd,"exit")){c.exitService(now);reply("OK");return;}
 if(!strcmp(cmd,"set")){
  char* key=strtok(nullptr," ");float value;
  if(!key||!number(strtok(nullptr," "),value)||strtok(nullptr," ")){reply("ERR syntax");return;}
  Settings proposed=c.settings;bool found=false;
  for(const Field& f:fields)if(!strcmp(key,f.name)){
   if(f.kind){if(value<0||value>255||floorf(value)!=value){reply("ERR integer required");return;}*(uint8_t*)((uint8_t*)&proposed+f.offset)=uint8_t(value);}
   else *(float*)((uint8_t*)&proposed+f.offset)=value;found=true;break;
  }
  if(!found||!valid(proposed)){reply("ERR unknown key or unsafe value");return;}
  proposed.commissioned=0;c.settings=proposed;c.markChanged(now);reply("OK recommission required");return;
 }
 if(!strcmp(cmd,"fan")){float v;bool ok=number(strtok(nullptr," "),v)&&v>=0&&v<=100&&c.testFan(v/100,now);reply(ok?"OK fan test expires in 10s":"ERR range");return;}
 if(!strcmp(cmd,"jog")){float v;bool ok=number(strtok(nullptr," "),v)&&floorf(v)==v&&v>=-10&&v<=10&&c.jogServo(int(v),now);reply(ok?"OK servo powered for 0.8s":"ERR max 10us per jog");return;}
 if(!strcmp(cmd,"capture")){
  float v;if(!number(strtok(nullptr," "),v)||v<0||v>4||floorf(v)!=v||!c.out.servoEnable||c.out.fanEnable){reply("ERR jog and hold at measured angle first");return;}
  int i=int(v);c.settings.servoUs[i]=c.out.servoUs;c.settings.feedback[i]=hw.in.servoAdc;c.settings.commissioned=0;c.markChanged(now);reply("OK captured pulse/feedback; all five points required");return;
 }
 if(!strcmp(cmd,"zero")){
  if(c.out.fanEnable||hw.in.rpm>60||!hw.in.pressureValid||fabsf(hw.in.pressurePa)>2){reply("ERR fan must stop, pressure valid and within 2Pa");return;}
  c.settings.pressureZero=hw.in.pressurePa;c.settings.commissioned=0;c.markChanged(now);reply("OK");return;
 }
 if(!strcmp(cmd,"led")){
  float v[4];for(int i=0;i<4;i++)if(!number(strtok(nullptr," "),v[i])||floorf(v[i])!=v[i]){reply("ERR syntax");return;}
  reply(lights.test(int(v[0]),int(v[1]),int(v[2]),int(v[3]),now)?"OK":"ERR bounds");return;
 }
 if(!strcmp(cmd,"format")){
  char* yes=strtok(nullptr," ");if(!yes||strcmp(yes,"ERASE")||c.out.fanEnable||c.out.servoEnable){reply("ERR loads must be off; format ERASE");return;}
  reply(storage.format()?"OK blank settings filesystem":"ERR format");c.settings.commissioned=0;return;
 }
 if(!strcmp(cmd,"commit")){
  char* yes=strtok(nullptr," ");Settings proposed=c.settings;proposed.commissioned=1;
  if(!yes||strcmp(yes,"MEASURED")||!valid(proposed)||c.out.fanEnable||c.out.servoEnable||!hw.in.pd15v||!hw.in.tempsValid||!hw.in.pressureValid||!hw.in.guardClosed||hw.in.tempPower>proposed.warnC-5||hw.in.tempMotor>proposed.warnC-5){reply("ERR finish measurements; stop loads; check sensors");return;}
  if(storage.save(proposed)){c.settings=proposed;c.settingsDirty=false;reply("OK calibrated settings saved and verified");}else reply("ERR storage; format only on first commissioning");return;
 }
 reply("ERR command");
}
void Service::poll(uint32_t now,Control& c,const Hardware& hw,Lighting& lights,Storage& storage){
 // Bounded work per loop; a flooded USB console cannot starve safety.
 for(int n=0;n<24&&Serial.available();n++){
  char b=Serial.read();if(b=='\r')continue;
  if(b=='\n'){if(!overflow_){line_[length_]=0;command(line_,now,c,hw,lights,storage);}else reply("ERR line too long");length_=0;overflow_=false;}
  else if(length_<sizeof(line_)-1&&!overflow_)line_[length_++]=b;else overflow_=true;
 }
}
}
