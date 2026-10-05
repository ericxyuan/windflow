#include <Arduino.h>
#include "Service.h"
#include <stdlib.h>
#include <string.h>
using namespace wf;
ServiceSerial Serial;
static int checks=0,saveCalls=0;
static bool saveSuccess=true;
static Settings saved;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %s:%d %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
namespace wf {
bool Storage::save(const Settings& s){saveCalls++;if(saveSuccess)saved=s;return saveSuccess;}
bool Storage::format(){return true;}
bool Lighting::test(int,int,int,int,uint32_t){return true;}
bool Display::test(uint8_t,uint32_t){return true;}
}
struct Rig {
 Service service;Control control;Hardware hardware;Lighting lights;Storage storage;uint32_t now=0;
 explicit Rig(bool commissioned=true){
  Serial.input.clear();Serial.output.clear();saveCalls=0;saveSuccess=true;
  control.settings.commissioned=commissioned;control.begin(0);control.enterService(0);
  auto& in=hardware.in;
  in.pd15v=in.tempsValid=in.pressureValid=in.guardClosed=in.fanPowerGood=in.servoPowerGood=true;
  in.busV=15;in.logicV=5;in.tempPower=in.tempMotor=25;in.pressurePa=.4f;in.rpm=0;in.servoAdc=600;
  wait(50);
 }
 void wait(uint32_t duration){for(uint32_t n=0;n<duration;n+=50){now+=50;service.poll(now,control,hardware,lights,storage);}}
 std::string command(const char* text){
  Serial.input=text;Serial.input+='\n';Serial.output.clear();
  while(Serial.available()){now++;service.poll(now,control,hardware,lights,storage);}
  return Serial.output;
 }
 void capture(int position){
  control.out.fanEnable=false;control.out.servoEnable=true;
  control.out.servoUs=uint16_t(1100+100*position);hardware.in.servoAdc=uint16_t(600+150*position);
  wait(450);char cmd[32];snprintf(cmd,sizeof(cmd),"capture %d",position);
  CHECK(command(cmd).find("OK captured")!=std::string::npos);
 }
 void completeEvidence(){
  wait(1200);CHECK(command("zero").find("OK pressure zero")!=std::string::npos);
  for(int i=0;i<5;i++)capture(i);
  control.out.servoEnable=false;control.out.fanEnable=true;control.out.pwm=control.settings.minPwm;hardware.in.rpm=360;wait(5600);
  CHECK(command("measure fan-min").find("OK minimum")!=std::string::npos);
  control.out.pwm=control.settings.maxPwm;hardware.in.rpm=1775;wait(5600);
  CHECK(command("measure fan-max").find("OK measured")!=std::string::npos);
  control.out.fanEnable=false;control.out.pwm=0;hardware.in.rpm=0;
 }
};
int main(){
 {Rig r;Settings original=r.control.settings;
  for(const char* command:{"set mainBrightness 50","set ambientBrightness 24","set nightMain 2","set nightAmbient 1"}){
   CHECK(r.command(command).find("calibration retained")!=std::string::npos);
   CHECK(r.control.settings.commissioned==1);CHECK(r.control.settingsDirty);CHECK(saveCalls==0);
   CHECK(!memcmp(r.control.settings.servoUs,original.servoUs,sizeof(original.servoUs)));
   CHECK(!memcmp(r.control.settings.feedback,original.feedback,sizeof(original.feedback)));
   CHECK(r.control.settings.pressureZero==original.pressureZero);CHECK(r.control.settings.rpmAtMax==original.rpmAtMax);
  }
  CHECK(r.command("commit MEASURED").find("OK calibrated settings saved")!=std::string::npos);
  CHECK(saveCalls==1);CHECK(saved.commissioned==1);CHECK(saved.mainBrightness==50);CHECK(saved.ambientBrightness==24);CHECK(saved.nightMain==2);CHECK(saved.nightAmbient==1);CHECK(!r.control.settingsDirty);
 }
 // Cosmetic changes preserve partial current-session evidence without turning
 // an uncommissioned/captured profile into a commissioned profile.
 {Rig r;r.capture(0);std::string before=r.command("evidence");CHECK(before.find("captures=0x01")!=std::string::npos);
  CHECK(r.command("set mainBrightness 40").find("calibration retained")!=std::string::npos);
  CHECK(r.control.settings.commissioned==0);CHECK(r.command("evidence")==before);
  r.control.out.servoEnable=false;CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);CHECK(saveCalls==0);
 }
 {Rig r(false);CHECK(r.command("set nightMain 3").find("calibration retained")!=std::string::npos);CHECK(r.control.settings.commissioned==0);CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);CHECK(saveCalls==0);}
 // Every supported geometry, fan, safety, direction and physical LED-count key
 // still invalidates commissioning; complete old evidence cannot be reused.
 for(const char* change:{"set boostThreshold 0.8","set minAreaRatio 0.8","set minPwm 0.25","set maxPwm 0.9","set rpmAtMax 1700","set pressureSoft 17","set pressureHard 23","set warnC 54","set tripC 64","set busScale 11.2","set logicScale 2.15","set encoderReverse 1","set ambientCount 7"}){
  Rig r;CHECK(r.command(change).find("recommission required")!=std::string::npos);CHECK(r.control.settings.commissioned==0);CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);CHECK(saveCalls==0);
 }
 {Rig r;r.completeEvidence();std::string before=r.command("evidence");CHECK(before.find("captures=0x1f zero=1 fanMin=1 fanMax=1")!=std::string::npos);
  CHECK(r.command("set ambientBrightness 30").find("calibration retained")!=std::string::npos);CHECK(r.command("evidence")==before);
  CHECK(r.control.settings.commissioned==0);CHECK(r.command("commit MEASURED").find("OK calibrated settings saved")!=std::string::npos);CHECK(saveCalls==1);CHECK(saved.commissioned==1);CHECK(saved.ambientBrightness==30);CHECK(saved.rpmAtMax==1775);
 }
 {Rig r;r.completeEvidence();CHECK(r.command("set encoderReverse 1").find("recommission required")!=std::string::npos);CHECK(r.command("evidence").find("captures=0x00 zero=0 fanMin=0 fanMax=0")!=std::string::npos);CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);CHECK(saveCalls==0);}
 for(const char* bad:{"set mainBrightness 81","set ambientBrightness 61","set nightMain 5","set nightAmbient 5","set mainBrightness -1","set mainBrightness 3.5","set mainBrightness nan","set mainBrightness inf","set mainBrightness 40 extra","set noSuchKey 1"}){
  Rig r;Settings before=r.control.settings;CHECK(r.command(bad).find("ERR")!=std::string::npos);CHECK(r.control.settings.commissioned==1);CHECK(r.control.settings.mainBrightness==before.mainBrightness);CHECK(r.control.settings.ambientBrightness==before.ambientBrightness);CHECK(r.control.settings.nightMain==before.nightMain);CHECK(r.control.settings.nightAmbient==before.nightAmbient);CHECK(!r.control.settingsDirty);CHECK(saveCalls==0);
 }
 // Retaining calibration never relaxes the existing save interlocks.
 {Rig r;CHECK(r.command("set mainBrightness 40").find("OK")!=std::string::npos);
  r.control.out.fanEnable=true;CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);r.control.out.fanEnable=false;
  r.control.out.servoEnable=true;CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);r.control.out.servoEnable=false;
  r.hardware.in.guardClosed=false;CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);r.hardware.in.guardClosed=true;
  r.hardware.in.pd15v=false;CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);r.hardware.in.pd15v=true;
  r.hardware.in.busV=14;CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);r.hardware.in.busV=15;
  r.hardware.in.tempPower=60;CHECK(r.command("commit MEASURED").find("ERR")!=std::string::npos);r.hardware.in.tempPower=25;
  CHECK(saveCalls==0);saveSuccess=false;CHECK(r.command("commit MEASURED").find("ERR storage")!=std::string::npos);CHECK(saveCalls==1);CHECK(r.control.settingsDirty);CHECK(r.control.settings.commissioned==1);
 }
 {Rig r;r.control.exitService(r.now);Settings before=r.control.settings;CHECK(r.command("set mainBrightness 40").find("ERR fit service")!=std::string::npos);CHECK(r.control.settings.mainBrightness==before.mainBrightness);CHECK(saveCalls==0);}
 printf("PASS %d service command assertions; cosmetic calibration retention/save, mechanical invalidation, evidence integrity, syntax/bounds, save interlocks\n",checks);return 0;
}
