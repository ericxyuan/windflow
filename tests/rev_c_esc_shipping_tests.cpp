#include "Control.h"
#include <cstdio>
#include <cstdlib>
using namespace wf;
int main(){
 if(kMotionBuildQualified)return 1;
 Control c;Inputs in;c.settings.on=1;c.settings.commissioned=1;c.settings.rotorQualified=1;
 in.pd15v=in.tempsValid=in.pressureValid=in.guardClosed=in.motorPowerGood=in.servoPowerGood=in.escTelemetryValid=true;
 in.busV=in.escVoltage=15;in.logicV=5;in.tempPower=in.tempMotor=in.escFetC=25;in.servoAdc=600;
 c.begin(0);for(uint32_t now=10;now<=10000;now+=10){c.tick(now,in);if(c.out.motorEnable||c.out.speedFraction!=0)return 2;}
 if(c.state!=State::Uncommissioned)return 3;
 c.enterService(10000);if(c.testMotor(.1,10000))return 4;if(!c.testMotor(0,10000))return 5;
 std::puts("PASS Rev C distributed build cannot request rotor motion");return 0;
}
