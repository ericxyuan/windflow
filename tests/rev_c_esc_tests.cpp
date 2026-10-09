#include "Control.h"
#include "VescProtocol.h"
#include "SensorCodec.h"
#include "SettingsRecord.h"
#include "DisplayView.h"
#include <cstdio>
#include <cstdlib>
#include <limits>
using namespace wf;
static int checks=0;
#define CHECK(x) do{checks++;if(!(x)){std::printf("FAIL %d %s\n",__LINE__,#x);std::exit(1);}}while(0)
static void put16(uint8_t* b,int16_t v){b[0]=uint8_t(uint16_t(v)>>8);b[1]=uint8_t(v);}
static void values(uint8_t* b){for(int i=0;i<54;i++)b[i]=0;b[0]=4;put16(b+1,250);put16(b+3,0);vescPut32(b+5,100);vescPut32(b+9,50);put16(b+21,100);vescPut32(b+23,21000);put16(b+27,150);}
struct Rig{
 Control c;Inputs in;uint32_t now=0;
 Rig(){c.settings.on=1;c.settings.commissioned=1;c.settings.rotorQualified=1;in.pd15v=true;in.tempsValid=true;in.pressureValid=true;in.guardClosed=true;in.motorPowerGood=true;in.servoPowerGood=true;in.escTelemetryValid=true;in.escFetC=25;in.escVoltage=15;in.escInputA=.5;in.escPhaseA=1;in.busV=15;in.logicV=5;in.tempPower=25;in.tempMotor=25;in.pressurePa=3;in.servoAdc=600;c.begin(0);}
 void step(uint32_t ms,bool followRpm=true){for(uint32_t t=0;t<ms;t+=10){now+=10;in.servoAdc=(uint16_t)c.feedbackTarget();if(followRpm)in.rpm=c.out.speedFraction*c.settings.rpmAtMax;c.tick(now,in);}}
 void live(){step(6000);CHECK(c.state==State::Live);}
 void boost(){c.settings.setting=750;live();CHECK(c.boostEntryReady());c.rotate(24);CHECK(c.rotaryMode()==RotaryMode::Boost);c.rotate(24);step(3500);CHECK(c.out.closure>.95);}
};
int main(){
 uint8_t b[54],frame[140];values(b);EscTelemetry t;VescParser p;
 size_t n=vescFrame(b,54,frame,sizeof(frame));CHECK(n==59);bool received=false;for(size_t i=0;i<n;i++)received=p.feed(frame[i],100,t)||received;
 CHECK(received);CHECK(t.fresh(400));CHECK(!t.fresh(401));CHECK(t.mechanicalRpm()==3000);CHECK(t.inputA==.5f);CHECK(t.fetC==25);
 CHECK(vescCrc((const uint8_t*)"123456789",9)==0x31c3); // Independent CCITT/XMODEM vector.
 EscTelemetry unchanged=t;frame[12]^=1;received=false;for(size_t i=0;i<n;i++)received=p.feed(frame[i],200,t)||received;CHECK(!received);CHECK(t.receivedAt==unchanged.receivedAt);CHECK(p.rejected==1);
 values(b);n=vescFrame(b,54,frame,sizeof(frame));frame[n-1]=4;for(size_t i=0;i<n;i++)CHECK(!p.feed(frame[i],300,t));CHECK(t.receivedAt==100);
 // Length-zero and oversized short/long packets do not write the fixed buffer.
 CHECK(!p.feed(2,400,t));CHECK(!p.feed(0,400,t));CHECK(!p.feed(2,400,t));CHECK(!p.feed(129,400,t));CHECK(!p.feed(3,400,t));CHECK(!p.feed(1,400,t));CHECK(!p.feed(0,400,t));
 n=vescFrame(b,54,frame,sizeof(frame));received=false;for(size_t i=0;i<n;i++)received=p.feed(frame[i],500,t)||received;CHECK(received&&t.receivedAt==500);
 // Gap expiry: a truncated packet cannot consume bytes forever or refresh data.
 p.feed(2,600,t);p.feed(54,600,t);p.feed(4,600,t);CHECK(!p.feed(0,621,t));CHECK(!t.fresh(801));
 // Valid long framing uses the same prefix/CRC and permits bounded extensions.
 uint8_t longFrame[60];longFrame[0]=3;longFrame[1]=0;longFrame[2]=54;for(size_t i=2;i<n;i++)longFrame[i+1]=frame[i];received=false;for(size_t i=0;i<60;i++)received=p.feed(longFrame[i],900,t)||received;CHECK(received);
 values(b);b[0]=8;CHECK(!decodeVescValues(b,54,950,t));CHECK(t.receivedAt==900);b[0]=4;CHECK(!decodeVescValues(b,53,950,t));put16(b+27,-150);CHECK(!decodeVescValues(b,54,950,t));
 values(b);vescPut32(b+23,-700);CHECK(decodeVescValues(b,54,1000,t));CHECK(t.mechanicalRpm()==-100);
 n=vescSpeedFrame(3000,7,3000,frame,sizeof(frame));CHECK(n==10&&frame[2]==8);CHECK(vescI32(frame+3)==21000);
 n=vescSpeedFrame(0,7,3000,frame,sizeof(frame));CHECK(n==10&&frame[2]==6&&vescI32(frame+3)==0); // Coast, never RPM-zero braking.
 CHECK(!vescSpeedFrame(-1,7,3000,frame,sizeof(frame)));CHECK(!vescSpeedFrame(3001,7,3000,frame,sizeof(frame)));CHECK(!vescSpeedFrame(1,6,3000,frame,sizeof(frame)));CHECK(!vescSpeedFrame(1,7,5001,frame,sizeof(frame)));CHECK(!vescSpeedFrame(NAN,7,3000,frame,sizeof(frame)));CHECK(!vescFrame(b,54,frame,58));
 CHECK(!decodePd(0x46,0x40));CHECK(decodePd(0x4a,0x40));CHECK(!decodePd(0x4a,0));CHECK(!decodePd(0x5a,0x40));
 Settings s;CHECK(valid(s));CHECK(!s.on&&!s.commissioned&&!s.rotorQualified);CHECK(kSchema==4);
 s.on=1;float previous=0;for(int i=0;i<=1000;i++){s.setting=i;Mapping m=mapSetting(s);CHECK(m.speedFraction>=previous-.000001f);CHECK(m.closure>=0&&m.closure<=1.00001f);CHECK(m.areaRatio>=.74999f);if(i<=750)CHECK(m.closure==0);else CHECK(m.speedFraction==1);previous=m.speedFraction;}
 s=Settings{};s.rpmAtMax=5001;CHECK(!valid(s));s=Settings{};s.escInputLimitA=1.41;CHECK(!valid(s));s=Settings{};s.escPhaseLimitA=3.01;CHECK(!valid(s));s=Settings{};s.escPowerLimitW=18.01;CHECK(!valid(s));s=Settings{};s.rpmAtMax=NAN;CHECK(!valid(s));
 auto record=makeRecord(Settings{},7);SettingsRecord decoded{};CHECK(decodeRecord(&record,sizeof(record),decoded));record.schema=3;record.crc=crc32(&record,offsetof(SettingsRecord,crc));CHECK(!decodeRecord(&record,sizeof(record),decoded));
 {Rig r;r.live();r.in.escTelemetryValid=false;r.step(10);CHECK(r.c.fault==Fault::EscTelemetry&&!r.c.out.motorEnable&&!r.c.out.escSupplyEnable);}
 {Rig r;r.live();r.in.rpm=3301;r.step(10,false);CHECK(r.c.fault==Fault::Overspeed);}
 {Rig r;r.live();r.in.rpm=-100;r.step(10,false);CHECK(r.c.fault==Fault::ReverseRotation);}
 {Rig r;r.live();r.in.escInputA=-.11;r.step(10);CHECK(r.c.fault==Fault::ReverseRotation);}
 {Rig r;r.live();r.in.escPhaseA=3.1;r.step(10);CHECK(r.c.fault==Fault::MotorCurrent);}
 {Rig r;r.live();r.in.escInputA=1.35;r.step(10);CHECK(r.c.fault==Fault::MotorCurrent);}
 {Rig r;r.live();r.in.escFault=4;r.step(10);CHECK(r.c.fault==Fault::EscController);}
 {Rig r;r.live();r.in.escFetC=66;r.step(10);CHECK(r.c.fault==Fault::Overtemperature);}
 {Rig r;r.live();r.in.escVoltage=13;r.step(10);CHECK(r.c.fault==Fault::Power);}
 {Rig r;r.live();r.in.escDuty=NAN;r.step(10);CHECK(r.c.fault==Fault::EscTelemetry);}
 {Rig r;r.c.settings.rotorQualified=0;r.step(6000);CHECK(r.c.state==State::Uncommissioned&&!r.c.out.motorEnable);}
 {Rig r;r.c.settings.commissioned=0;r.step(6000);CHECK(r.c.state==State::Uncommissioned&&!r.c.out.motorEnable);}
 {Rig r;r.in.escTelemetryValid=false;r.step(6000);CHECK(r.c.state==State::WaitPower&&!r.c.out.motorEnable);}
 {Rig r;r.c.settings.setting=750;r.live();CHECK(r.c.boostEntryReady());r.c.rotate(23);CHECK(r.c.rotaryMode()==RotaryMode::BoostEntry&&r.c.entryDetentsRemaining()==1);r.c.rotate(1);CHECK(r.c.rotaryMode()==RotaryMode::Boost);r.c.rotate(12);r.step(1800);CHECK(r.c.out.closure>.45&&r.c.out.closure<.6);r.c.rotate(-12);CHECK(r.c.rotaryMode()==RotaryMode::BoostEntry&&r.c.entryDetentsRemaining()==24);r.step(2000);r.c.rotate(23);CHECK(r.c.rotaryMode()!=RotaryMode::Boost);r.c.rotate(1);CHECK(r.c.rotaryMode()==RotaryMode::Boost);}
 {Rig r;r.c.settings.setting=1000;r.live();CHECK(r.c.settings.setting==750&&r.c.rotaryMode()==RotaryMode::BoostEntry&&r.c.out.closure==0);}
 {Rig r;r.boost();r.in.pressurePa=20;r.step(1400);CHECK(r.c.out.closure<.05&&r.c.out.boostLimited);}
 {Rig r;r.boost();r.in.tempPower=56;r.step(1200);CHECK(r.c.out.thermal&&r.c.out.closure<.05&&r.c.out.speedFraction<=.5);}
 {Rig r;r.live();r.in.guardClosed=false;r.step(10);CHECK(r.c.fault==Fault::Guard&&!r.c.out.escSupplyEnable);}
 {Rig r;r.live();r.c.longPress();r.step(10);CHECK(r.c.settings.night&&r.c.out.motorEnable);r.c.shortPress();r.step(10);CHECK(!r.c.out.motorEnable&&r.c.out.speedFraction==0);}
 {Rig r;r.live();r.in.rpm=0;r.step(4000,false);CHECK(r.c.fault==Fault::Stall);}
 {Rig r;r.live();r.c.enterService(r.now);r.step(10);CHECK(r.c.testMotor(.3,r.now));r.step(10100);CHECK(!r.c.out.motorEnable);}
 {Rig r;r.live();r.c.enterService(r.now);r.step(10);CHECK(r.c.testMotor(.3,r.now));r.step(100);CHECK(r.c.out.motorEnable&&r.c.out.servoEnable&&r.c.out.servoUs==r.c.settings.servoUs[0]);CHECK(r.c.testMotor(0,r.now));r.in.rpm=200;r.step(10,false);CHECK(!r.c.out.motorEnable&&r.c.out.servoEnable);r.in.rpm=0;r.step(10,false);CHECK(!r.c.out.servoEnable);}
 {Rig r;r.live();r.c.enterService(r.now);r.in.rpm=200;CHECK(r.c.jogServo(5,r.now));r.step(10,false);CHECK(!r.c.out.servoEnable);}
 {Rig r;r.live();r.in.escFault=1;r.step(10);r.in.rpm=200;CHECK(!r.c.acknowledge(r.now,r.in));r.in.rpm=-200;CHECK(!r.c.acknowledge(r.now,r.in));r.in.rpm=std::numeric_limits<float>::quiet_NaN();CHECK(!r.c.acknowledge(r.now,r.in));r.in.rpm=0;CHECK(r.c.acknowledge(r.now,r.in));CHECK(!r.c.settings.on);}
 std::printf("PASS Rev C parser/safety/control/display %d checks\n",checks);return 0;
}
