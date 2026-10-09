#include <Arduino.h>
#include "Service.h"
#include <stdlib.h>
#include <string.h>
using namespace wf;
ServiceSerial Serial;
static int checks=0,saves=0;static Settings saved;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL line%d %s\n",__LINE__,#x);exit(1);}}while(0)
namespace wf {
bool Storage::save(const Settings& s){saved=s;saves++;return true;}
bool Storage::format(){return true;}
bool Lighting::test(int,int,int,int,uint32_t){return true;}
bool Display::test(uint8_t,uint32_t){return true;}
}
struct Rig {
 Service service;Control c;Hardware hw;Lighting lights;Storage storage;uint32_t now=0;
 Rig(){Serial.input.clear();Serial.output.clear();saves=0;c.settings.rotorQualified=1;c.settings.commissioned=1;c.begin(0);c.enterService(0);auto& in=hw.in;in.pd15v=in.tempsValid=in.pressureValid=in.guardClosed=in.motorPowerGood=in.servoPowerGood=in.escTelemetryValid=true;in.busV=in.escVoltage=15;in.logicV=5;in.tempPower=in.tempMotor=in.escFetC=25;in.pressurePa=.4;in.servoAdc=600;wait(50);}
 void wait(uint32_t ms){for(uint32_t t=0;t<ms;t+=50){now+=50;service.poll(now,c,hw,lights,storage);}}
 std::string cmd(const char* s){Serial.input=s;Serial.input+='\n';Serial.output.clear();while(Serial.available()){now++;service.poll(now,c,hw,lights,storage);}return Serial.output;}
 void capture(int i){c.out.motorEnable=false;c.out.servoEnable=true;c.out.servoUs=uint16_t(1100+100*i);hw.in.servoAdc=uint16_t(600+150*i);wait(450);char b[32];snprintf(b,sizeof(b),"capture %d",i);CHECK(cmd(b).find("OK captured")!=std::string::npos);}
};
int main(){
 {Rig r;CHECK(r.cmd("esc").find("escFresh=1")!=std::string::npos);CHECK(r.cmd("fan 10").find("ERR command")!=std::string::npos);CHECK(r.cmd("motor 10").find("ERR")!=std::string::npos);CHECK(r.cmd("motor -1").find("ERR")!=std::string::npos);CHECK(r.cmd("motor nan").find("ERR")!=std::string::npos);}
 {Rig r;for(const char* s:{"set mainBrightness 50","set ambientBrightness 20","set nightMain 2","set nightAmbient 1"}){CHECK(r.cmd(s).find("calibration retained")!=std::string::npos);CHECK(r.c.settings.commissioned&&r.c.settings.rotorQualified);}
  auto response=r.cmd("commit MEASURED");CHECK((response.find("OK calibrated")!=std::string::npos)==kMotionBuildQualified);CHECK(saves==(kMotionBuildQualified?1:0));}
 for(const char* field:{"set rpmAtMax 2500","set escInputLimitA 1.2","set escPhaseLimitA 2","set escPowerLimitW 18"}){Rig r;CHECK(r.cmd(field).find("recommission")!=std::string::npos);CHECK(!r.c.settings.commissioned&&!r.c.settings.rotorQualified);CHECK(r.cmd("commit MEASURED").find("ERR")!=std::string::npos);CHECK(saves==0);}
 for(const char* s:{"set rpmAtMax 5001","set escInputLimitA 1.41","set escPhaseLimitA 3.1","set escPowerLimitW 21","set rotorQualified 1","set commissioned 1","set minSpeedFraction nan","rotor YES","rotor CONTAINED_QUALIFIED extra"}){Rig r;CHECK(r.cmd(s).find("ERR")!=std::string::npos);CHECK(saves==0);}
 {Rig r;r.hw.in.escTelemetryValid=false;CHECK(r.cmd("rotor CONTAINED_QUALIFIED").find("ERR")!=std::string::npos);r.hw.in.escTelemetryValid=true;r.hw.in.rpm=200;CHECK(r.cmd("rotor CONTAINED_QUALIFIED").find("ERR")!=std::string::npos);r.hw.in.rpm=0;auto s=r.cmd("rotor CONTAINED_QUALIFIED");CHECK((s.find("OK physical")!=std::string::npos)==kMotionBuildQualified);}
 {Rig r;r.capture(0);r.c.out.servoEnable=false;auto s=r.cmd("motor 30");CHECK((s.find("OK RPM")!=std::string::npos)==kMotionBuildQualified);CHECK(r.cmd("motor 0").find("OK RPM")!=std::string::npos);}
 if(kMotionBuildQualified){
  Rig r;CHECK(r.cmd("rotor CONTAINED_QUALIFIED").find("OK physical")!=std::string::npos);CHECK(!r.c.settings.commissioned);r.wait(1200);CHECK(r.cmd("zero").find("OK pressure")!=std::string::npos);for(int i=0;i<5;i++)r.capture(i);
  r.c.out.servoEnable=true;r.c.out.servoUs=r.c.settings.servoUs[0];r.hw.in.servoAdc=r.c.settings.feedback[0];r.c.out.motorEnable=true;r.c.out.speedFraction=r.c.settings.minSpeedFraction;r.hw.in.rpm=r.c.settings.rpmAtMax*r.c.settings.minSpeedFraction;r.wait(5600);CHECK(r.cmd("measure motor-min").find("OK minimum")!=std::string::npos);
  r.c.out.speedFraction=r.c.settings.maxSpeedFraction;r.hw.in.rpm=r.c.settings.rpmAtMax*r.c.settings.maxSpeedFraction;r.wait(5600);CHECK(r.cmd("measure motor-max").find("OK maximum")!=std::string::npos);CHECK(r.c.settings.rpmAtMax==3000);
  r.c.out.motorEnable=false;r.c.out.servoEnable=false;r.c.out.speedFraction=0;r.hw.in.rpm=0;CHECK(r.cmd("commit MEASURED").find("OK calibrated")!=std::string::npos);CHECK(saves==1&&saved.commissioned&&saved.rotorQualified);
 }
 {Rig r;r.capture(0);r.hw.in.rpm=200;CHECK(r.cmd("capture 0").find("ERR")!=std::string::npos);}
 {Rig r;CHECK(r.cmd("format ERASE").find("OK blank")!=std::string::npos);CHECK(!r.c.settings.commissioned&&!r.c.settings.rotorQualified);}
 {Rig r;r.c.exitService(r.now);CHECK(r.cmd("rotor CONTAINED_QUALIFIED").find("ERR fit service")!=std::string::npos);}
 printf("PASS Rev C production service %d assertions (motion build flag %d)\n",checks,int(kMotionBuildQualified));return 0;
}
