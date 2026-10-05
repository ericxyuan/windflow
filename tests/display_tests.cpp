#include "DisplayView.h"
#include <limits>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
using namespace wf;
static int checks=0;
#define CHECK(x) do{checks++;if(!(x)){printf("FAIL %s:%d %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
static void live(Control& c,Inputs& in){
 c.settings.commissioned=1;c.begin(0);
 for(uint32_t now=10;now<=7000;now+=10){in.servoAdc=uint16_t(c.feedbackTarget());in.rpm=c.out.pwm*c.settings.rpmAtMax;c.tick(now,in);}
 CHECK(c.state==State::Live);
}
int main(){
 Control c;Inputs in;
 in.pd15v=in.tempsValid=in.pressureValid=in.guardClosed=in.fanPowerGood=in.servoPowerGood=true;
 in.busV=15;in.logicV=5;in.tempPower=31.23f;in.tempMotor=28.47f;in.pressurePa=3.47f;
 c.settings.setting=400;live(c,in);
 DisplayFrame f=displayFrame(c,in);
 CHECK(f.normalPercent==53);CHECK(f.normalDetentsLeft==12);CHECK(f.entryDegreesLeft==360);
 CHECK(f.dialDegrees==0);CHECK(f.nozzlePercent==100);CHECK(f.boostPercent==0);
 CHECK(f.temperatureTenths==312);CHECK(f.pressureTenths==35);CHECK(f.busTenths==150);
 CHECK(f.temperaturesValid&&f.pressureValid&&f.pdReady);
 CHECK(f==displayFrame(c,in));CHECK(!strcmp(displaySystemName(f),"15V USB-C READY"));
 CHECK(!strcmp(displayEntryInstruction(f),"Raise normal power to max."));
 c.rotate(12);for(uint32_t now=7010;now<=9000;now+=10){in.servoAdc=uint16_t(c.feedbackTarget());in.rpm=c.out.pwm*1800;c.tick(now,in);}
 f=displayFrame(c,in);CHECK(f.normalPercent==100);CHECK(f.normalDetentsLeft==0);CHECK(f.entryReady);
 for(int i=1;i<24;i++){
  c.rotate(1);DisplayFrame turn=displayFrame(c,in);
  CHECK(turn.entryDetents==i);CHECK(turn.entryDegreesLeft==(24-i)*15);
  CHECK(turn.dialDegrees==((12+i)%24)*15);CHECK(turn.boostPercent==0);CHECK(turn.nozzlePercent==100);
 }
 c.rotate(1);f=displayFrame(c,in);CHECK(f.mode==RotaryMode::Boost);CHECK(f.entryDegreesLeft==0);CHECK(f.boostPercent==0);
 c.rotate(12);c.out.closure=.5f;f=displayFrame(c,in);CHECK(f.boostPercent==50);CHECK(f.normalPercent==100);CHECK(f.nozzlePercent<100&&f.nozzlePercent>75);
 c.out.closure=1;f=displayFrame(c,in);CHECK(f.nozzlePercent==75);
 c.out.boostLimited=true;f=displayFrame(c,in);CHECK(f.limited);CHECK(!strcmp(displaySystemName(f),"BOOST LIMITED"));
 c.out.thermal=true;f=displayFrame(c,in);CHECK(f.thermal);CHECK(!strcmp(displaySystemName(f),"TEMP / BOOST OFF"));
 c.state=State::Fault;c.fault=Fault::Stall;f=displayFrame(c,in);CHECK(f.state==State::Fault&&f.fault==Fault::Stall);
 CHECK(!strcmp(displayFaultName(f.fault),"FAN STALL"));CHECK(!strcmp(displaySystemName(f),"FAULT / LOADS OFF"));
 DisplayFrame other=f;other.dialDegrees+=15;CHECK(!(f==other));other=f;other.pressureTenths++;CHECK(!(f==other));
 other=f;other.temperaturesValid=false;CHECK(!(f==other));
 for(unsigned fault=0;fault<=unsigned(Fault::Watchdog);fault++)CHECK(strlen(displayFaultName(Fault(fault)))>0);
 in.rpm=in.busV=in.tempPower=in.pressurePa=std::numeric_limits<float>::quiet_NaN();
 f=displayFrame(c,in);CHECK(f.rpm==0&&f.busTenths==0);CHECK(!f.temperaturesValid&&!f.pressureValid);
 in.rpm=in.busV=in.tempPower=in.pressurePa=std::numeric_limits<float>::infinity();
 f=displayFrame(c,in);CHECK(f.rpm==0&&f.busTenths==0);CHECK(!f.temperaturesValid&&!f.pressureValid);
 c.settings.minAreaRatio=std::numeric_limits<float>::quiet_NaN();f=displayFrame(c,in);CHECK(f.nozzlePercent==100);
 c.settings.minAreaRatio=.75;c.state=State::RampUp;c.out.animation=.375f;f=displayFrame(c,in);CHECK(f.normalPercent==38);
 {Control grid;Inputs sensors;grid.settings.setting=0;grid.begin(0);DisplayFrame start=displayFrame(grid,sensors);CHECK(start.normalDetentsLeft==24);CHECK(start.entryDegreesLeft+start.normalDetentsLeft*15==720);grid.rotate(1);DisplayFrame one=displayFrame(grid,sensors);CHECK(one.normalDetentsLeft==23);CHECK(one.entryDegreesLeft+one.normalDetentsLeft*15==705);grid.rotate(23);DisplayFrame maximum=displayFrame(grid,sensors);CHECK(maximum.normalDetentsLeft==0);CHECK(maximum.entryDegreesLeft==360);CHECK(!maximum.entryReady);CHECK(!strcmp(displayEntryInstruction(maximum),"Wait for startup."));}
 {Control grid;Inputs sensors;grid.settings.boostThreshold=.7555f;grid.settings.setting=400;grid.begin(0);DisplayFrame partial=displayFrame(grid,sensors);CHECK(partial.normalDetentsLeft==12);grid.rotate(1);partial=displayFrame(grid,sensors);CHECK(partial.normalDetentsLeft==11);grid.rotate(-1);partial=displayFrame(grid,sensors);CHECK(partial.normalDetentsLeft==12);}
 {DisplayFrame status;status.state=State::Live;status.on=true;status.entryReady=false;CHECK(!strcmp(displayEntryInstruction(status),"Opening outlet; wait."));status.outletReady=true;CHECK(!strcmp(displayEntryInstruction(status),"Reaching full power."));status.powerReady=true;CHECK(!strcmp(displayEntryInstruction(status),"Checking boost readiness."));status.normalDetentsLeft=1;CHECK(!strcmp(displayEntryInstruction(status),"Raise normal power to max."));status.normalDetentsLeft=0;status.entryReady=true;CHECK(!strcmp(displayEntryInstruction(status),"Turn UP to enter boost."));status.thermal=true;CHECK(!strcmp(displayEntryInstruction(status),"Boost paused by safety."));status.thermal=false;status.limited=true;CHECK(!strcmp(displayEntryInstruction(status),"Boost paused by safety."));status.limited=false;status.on=false;CHECK(!strcmp(displayEntryInstruction(status),"Press to start."));status.state=State::Service;CHECK(!strcmp(displayEntryInstruction(status),"Commission before boost."));status.state=State::Fault;CHECK(!strcmp(displayEntryInstruction(status),"Clear fault before boost."));}
 printf("PASS %d display view assertions\n",checks);return 0;
}
