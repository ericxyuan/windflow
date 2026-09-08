#include "Control.h"
#include "SensorCodec.h"
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
 {Rig r;r.live();r.in.servoAdc=3000;r.step(800,false);CHECK(r.c.fault==Fault::Servo);CHECK(!r.c.out.servoEnable);}
 {Rig r;r.in.servoAdc=3000;r.step(2500,false);CHECK(r.c.fault==Fault::Servo);}
 {Rig r;r.c.enterService(0);CHECK(r.c.jogServo(5,0));r.step(400);CHECK(r.c.out.servoEnable);r.step(500);CHECK(!r.c.out.servoEnable);CHECK(!r.c.jogServo(500,r.now));CHECK(r.c.testFan(.6,r.now));r.step(500);CHECK(r.c.out.fanEnable);r.in.tempsValid=false;r.step(10);CHECK(r.c.fault==Fault::TemperatureSensor);}
 {Rig r;r.c.enterService(0);CHECK(r.c.testFan(.5,0));r.step(10500);CHECK(!r.c.out.fanEnable);}
 {Rig r;r.c.begin(0,true);r.step(1000);CHECK(r.c.fault==Fault::Watchdog);CHECK(!r.c.out.fanEnable);}
 {Rig r;r.now=0xfffff000;r.c.begin(r.now);r.step(7000);CHECK(r.c.state==State::Live);}
 CHECK(decodePd(0x46,0x40));CHECK(!decodePd(0x36,0x40));CHECK(!decodePd(0x44,0x40));CHECK(!decodePd(0x46,0));
 CHECK(fabsf(decodeMcp(0x0190)-25)<.01);CHECK(fabsf(decodeMcp(0x1ff0)+1)<.01);
 uint8_t b[9]={0x09,0x60,0,0x13,0x88,0,0,240,0};for(int j=0;j<9;j+=3)b[j+2]=crc8(b+j,2);float pa=0;CHECK(decodePressure(b,pa));CHECK(fabsf(pa-10)<.001);b[0]^=1;CHECK(!decodePressure(b,pa));
 CHECK(crc32("123456789",9)==0xcbf43926u);
 printf("PASS %d assertions; control mapping, startup, thermal, power, pressure, tach, servo, service, rollover, sensor codecs\n",checks);
}
