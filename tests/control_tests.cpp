#include "Control.h"
#include "SensorCodec.h"
#include "Calibration.h"
#include "SettingsRecord.h"
#include <stdio.h>
#include <stdlib.h>
#include <limits>
using namespace wf;
static int checks=0;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %s:%d %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
struct Rig{
 Control c;Inputs in;uint32_t now=0;
 Rig(){c.settings.commissioned=1;in.pd15v=true;in.tempsValid=true;in.pressureValid=true;in.guardClosed=true;in.fanPowerGood=true;in.servoPowerGood=true;in.busV=15;in.logicV=5;in.tempPower=25;in.tempMotor=25;in.pressurePa=3;in.servoAdc=600;c.begin(0);}
 void step(uint32_t duration,bool follow=true,bool tach=true){for(uint32_t t=0;t<duration;t+=10){now+=10;if(follow)in.servoAdc=(uint16_t)c.feedbackTarget();if(tach)in.rpm=c.out.pwm*c.settings.rpmAtMax;c.tick(now,in);}}
 void live(){step(7000);CHECK(c.state==State::Live);}
};
int main(){
 Settings s;CHECK(valid(s));CHECK(maxPanelAngle(s)>12&&maxPanelAngle(s)<13);
 float prevP=0,prevC=0;
 for(int i=0;i<=1000;i++){s.setting=i;Mapping m=mapSetting(s);CHECK(m.pwm>=prevP-.00001f);CHECK(m.closure>=prevC-.00001f);CHECK(m.areaRatio>=.74999f);CHECK(m.closure<=1.00001f);if(i<=750)CHECK(m.closure==0);else CHECK(m.pwm==1);prevP=m.pwm;prevC=m.closure;}
 s.on=0;CHECK(mapSetting(s).pwm==0&&mapSetting(s).closure==0);
 s=Settings{};s.boostThreshold=std::numeric_limits<float>::quiet_NaN();CHECK(!valid(s));
 s=Settings{};s.minAreaRatio=.1;CHECK(!valid(s));s=Settings{};s.servoUs[2]=2500;CHECK(!valid(s));
 s=Settings{};s.servoUs[2]=1000;CHECK(!valid(s));s=Settings{};s.mainCount=200;CHECK(!valid(s));
 {Rig r;r.c.settings.commissioned=0;r.step(3000);CHECK(r.c.state==State::Uncommissioned);CHECK(!r.c.out.fanEnable&&!r.c.out.servoEnable);}
 {Rig r;r.in.pd15v=false;r.step(3000);CHECK(r.c.state==State::WaitPower);CHECK(!r.c.out.fanEnable);}
 {Rig r;r.step(600);CHECK(r.c.state==State::Homing);CHECK(r.c.out.pwm==0);r.step(400);CHECK(r.c.state==State::RampUp);r.step(1700);CHECK(r.c.state==State::RampDown);CHECK(r.c.out.pwm>.99);r.step(1000);CHECK(r.c.state==State::Live);CHECK(fabsf(r.c.out.pwm-mapSetting(r.c.settings).pwm)<.02);}
 {Rig r;r.c.settings.night=1;r.step(1000);CHECK(r.c.state==State::Live);CHECK(r.c.out.pwm<.3);}
 {Rig r;r.c.settings.on=0;r.step(4000);CHECK(r.c.out.pwm==0&&!r.c.out.fanEnable);}
 {Rig r;r.c.settings.setting=0;for(int i=0;i<500;i++){r.step(10);CHECK(!r.c.out.fanEnable);CHECK(r.c.out.pwm==0);}CHECK(r.c.state==State::Live);}
 {Rig r;r.step(1500);r.c.settings.setting=0;r.step(10);CHECK(r.c.out.pwm==0&&!r.c.out.fanEnable);CHECK(r.c.state==State::Live);}
 {Rig r;r.c.settings.setting=1000;r.live();CHECK(r.c.out.closure>.95);CHECK(r.c.out.pwm>.99);}
 {Rig r;r.c.settings.setting=1000;r.live();r.in.pressurePa=20;r.step(1400);CHECK(r.c.out.closure<.05);CHECK(r.c.out.boostLimited);r.in.pressurePa=4;r.step(2000);CHECK(r.c.out.closure<.05);r.c.settings.setting=700;r.step(100);r.c.settings.setting=1000;r.step(3500);CHECK(r.c.out.closure>.95);}
 {Rig r;r.c.settings.setting=1000;r.live();r.in.pressureValid=false;r.step(1000);CHECK(r.c.out.closure<.05);CHECK(r.c.out.pwm<=.5001);CHECK(r.c.state==State::Live);}
 {Rig r;r.live();r.in.pressurePa=30;r.step(1500);CHECK(r.c.fault==Fault::Pressure);CHECK(!r.c.out.fanEnable);}
 {Rig r;r.c.settings.setting=1000;r.live();r.in.tempPower=56;r.step(1100);CHECK(r.c.out.thermal);CHECK(r.c.out.closure<.05);CHECK(r.c.out.pwm<=.5001);CHECK(!r.c.out.ledEnable);r.in.tempPower=53;r.step(100);CHECK(r.c.out.thermal);r.in.tempPower=49;r.step(100);CHECK(!r.c.out.thermal);}
 {Rig r;r.step(1500);CHECK(r.c.state==State::RampUp);r.in.tempPower=56;r.step(50);CHECK(r.c.out.pwm<=.5);CHECK(r.c.state==State::Live);}
 {Rig r;r.live();r.in.tempPower=66;r.step(10);CHECK(r.c.fault==Fault::Overtemperature);CHECK(!r.c.out.fanEnable&&!r.c.out.servoEnable);CHECK(!r.c.acknowledge(r.now,r.in));r.in.tempPower=25;CHECK(r.c.acknowledge(r.now,r.in));CHECK(r.c.settings.on==0);}
 {Rig r;r.live();r.in.tempsValid=false;r.step(10);CHECK(r.c.fault==Fault::TemperatureSensor);}
 {Rig r;r.live();r.in.busV=13;r.step(10);CHECK(r.c.fault==Fault::Power);CHECK(!r.c.out.fanEnable);}
 {Rig r;r.live();r.in.guardClosed=false;r.step(10);CHECK(r.c.fault==Fault::Guard);}
 {Rig r;r.live();r.in.rpm=0;r.step(1000,true,false);CHECK(r.c.fault==Fault::Stall);}
 {Rig r;r.live();r.in.guardClosed=false;r.step(10);r.in.guardClosed=true;CHECK(r.c.acknowledge(r.now,r.in));r.step(1200);CHECK(r.c.state==State::Live);r.c.shortPress();r.in.rpm=0;r.step(2200,true,false);CHECK(r.c.state==State::Live);r.step(1500,true,false);CHECK(r.c.fault==Fault::Stall);}
 {Rig r;r.live();r.in.guardClosed=false;r.step(10);r.in.guardClosed=true;r.in.logicV=4;CHECK(!r.c.acknowledge(r.now,r.in));r.in.logicV=5;r.in.tempPower=std::numeric_limits<float>::quiet_NaN();CHECK(!r.c.acknowledge(r.now,r.in));}
 {Rig r;r.live();r.in.servoAdc=3000;r.step(800,false);CHECK(r.c.fault==Fault::Servo);CHECK(!r.c.out.servoEnable);}
 {Rig r;r.in.servoAdc=3000;r.step(2500,false);CHECK(r.c.fault==Fault::Servo);}
 {Rig r;r.c.enterService(0);CHECK(r.c.jogServo(5,0));r.step(400);CHECK(r.c.out.servoEnable);r.step(500);CHECK(!r.c.out.servoEnable);CHECK(!r.c.jogServo(500,r.now));CHECK(r.c.testFan(.6,r.now));r.step(500);CHECK(r.c.out.fanEnable);r.in.tempsValid=false;r.step(10);CHECK(r.c.fault==Fault::TemperatureSensor);}
 {Rig r;r.c.enterService(0);CHECK(r.c.testFan(.5,0));r.step(10500);CHECK(!r.c.out.fanEnable);}
 {Rig r;r.c.enterService(0);CHECK(r.c.testFan(0,0));r.step(200);CHECK(!r.c.out.fanEnable&&!r.c.out.servoEnable);CHECK(r.c.jogServo(5,r.now));r.step(100);CHECK(r.c.out.servoEnable);CHECK(r.c.testFan(0,r.now));r.step(10);CHECK(!r.c.out.fanEnable&&!r.c.out.servoEnable);r.c.settings.maxPwm=.8f;CHECK(!r.c.testFan(1,r.now));}
 {Rig r;r.c.begin(0,true);r.step(1000);CHECK(r.c.fault==Fault::Watchdog);CHECK(!r.c.out.fanEnable);}
 {Rig r;r.now=0xfffff000;r.c.begin(r.now);r.step(7000);CHECK(r.c.state==State::Live);}
 CHECK(decodePd(0x46,0x40));CHECK(!decodePd(0x36,0x40));CHECK(!decodePd(0x44,0x40));CHECK(!decodePd(0x46,0));
 CHECK(fabsf(decodeMcp(0x0190)-25)<.01);CHECK(fabsf(decodeMcp(0x1ff0)+1)<.01);
 uint8_t b[9]={0x09,0x60,0,0x13,0x88,0,0,240,0};for(int j=0;j<9;j+=3)b[j+2]=crc8(b+j,2);float pa=0;CHECK(decodePressure(b,pa));CHECK(fabsf(pa-10)<.001);b[0]^=1;CHECK(!decodePressure(b,pa));
 CHECK(crc32("123456789",9)==0xcbf43926u);
 // Persistence codec: reject every truncation and single-bit corruption, and
 // retain the older valid slot when a simulated interrupted write damages the new one.
 {Settings original;original.commissioned=1;SettingsRecord old=makeRecord(original,55),parsed{},newer=makeRecord(original,56);
  CHECK(decodeRecord(&old,sizeof(old),parsed));CHECK(parsed.sequence==55);CHECK(parsed.settings.setting==400);
  for(size_t n=0;n<sizeof(old);n++)CHECK(!decodeRecord(&old,n,parsed));
  for(size_t n=0;n<offsetof(SettingsRecord,crc)+sizeof(uint32_t);n++){auto damaged=old;((uint8_t*)&damaged)[n]^=1;CHECK(!decodeRecord(&damaged,sizeof(damaged),parsed));}
  CHECK(newestRecord(true,old,true,newer)==1);CHECK(newestRecord(true,old,false,newer)==0);CHECK(newestRecord(false,old,true,newer)==1);CHECK(newestRecord(false,old,false,newer)==-1);
  newer=makeRecord(original,0);old=makeRecord(original,0xffffffffu);CHECK(newestRecord(true,old,true,newer)==1);CHECK(newestRecord(true,newer,true,newer)==0);
  newer.schema=kSchema-1;newer.crc=crc32(&newer,offsetof(SettingsRecord,crc));CHECK(!decodeRecord(&newer,sizeof(newer),parsed));
  original.minAreaRatio=.1f;auto unsafe=makeRecord(original,1);CHECK(!decodeRecord(&unsafe,sizeof(unsafe),parsed));
 }
 {Rig r;r.c.enterService(0);Calibration proof;uint32_t time=0;
  auto observe=[&](int duration){for(int i=0;i<duration;i+=50){time+=50;proof.observe(time,r.c,r.in);}};
  CHECK(!proof.complete());CHECK(!proof.zero(r.c.settings));CHECK(!proof.measureFan(true,r.c.settings));
  r.in.pressurePa=.4f;r.in.rpm=0;observe(1200);CHECK(proof.zero(r.c.settings));CHECK(fabsf(r.c.settings.pressureZero-.4f)<.001f);
  r.c.out.servoEnable=true;r.c.out.servoUs=1100;r.in.servoAdc=600;CHECK(!proof.capture(0,r.c.settings,r.c.out,r.in));
  for(int i=0;i<5;i++){r.c.out.servoUs=1100+i*100;r.in.servoAdc=600+i*150;observe(400);CHECK(proof.capture(i,r.c.settings,r.c.out,r.in));}
  CHECK(proof.captures==31);CHECK(!proof.complete());CHECK(valid(r.c.settings));
  r.c.out.servoEnable=false;r.c.out.fanEnable=true;r.c.out.pwm=r.c.settings.minPwm;r.in.rpm=360;observe(5200);CHECK(proof.measureFan(false,r.c.settings));CHECK(!proof.measureFan(true,r.c.settings));
  r.c.out.pwm=r.c.settings.maxPwm;r.in.rpm=1775;observe(5200);CHECK(proof.measureFan(true,r.c.settings));CHECK(fabsf(r.c.settings.rpmAtMax-1775)<.001f);CHECK(proof.complete());proof.reset();CHECK(!proof.complete()&&proof.captures==0);
  r.c.out.fanEnable=false;r.c.out.servoEnable=false;r.in.rpm=0;r.in.pressurePa=1;observe(600);r.in.pressurePa=-1;observe(600);CHECK(!proof.zero(r.c.settings));
 }
 printf("PASS %d assertions; mapping, startup, fault recovery, pressure, tach, servo, service, calibration evidence, storage corruption/partial records, rollover, codecs\n",checks);
}
