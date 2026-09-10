#pragma once
#include "Config.h"
namespace wf {
enum class State:uint8_t {WaitPower,Uncommissioned,Homing,RampUp,RampDown,Live,Service,Fault};
enum class Fault:uint8_t {None,Power,TemperatureSensor,Overtemperature,Stall,Servo,Pressure,Guard,Watchdog};
struct Inputs {
 bool pd15v=false,tempsValid=false,pressureValid=false,guardClosed=false;
 bool fanPowerGood=false,servoPowerGood=false;
 float busV=0,logicV=0,tempPower=0,tempMotor=0,pressurePa=0,rpm=0;
 uint16_t servoAdc=0;
};
struct Outputs {
 float pwm=0,closure=0,animation=0;
 uint16_t servoUs=1500;
 bool fanEnable=false,servoEnable=false,ledEnable=false,boostLimited=false,thermal=false;
};
class Control {
public:
 Settings settings{};
 Outputs out{};
 State state=State::WaitPower;
 Fault fault=Fault::None;
 void begin(uint32_t now,bool watchdogReset=false);
 void tick(uint32_t now,const Inputs& in);
 void rotate(int detents);
 void shortPress();
 void longPress();
 void enterService(uint32_t now);
 void exitService(uint32_t now);
 bool testFan(float duty,uint32_t now);
 bool jogServo(int delta,uint32_t now);
 bool acknowledge(uint32_t now,const Inputs& in);
 float feedbackTarget()const;
 bool settingsDirty=false;
 uint32_t changedAt=0;
 void markChanged(uint32_t now){settingsDirty=true;changedAt=now;}
private:
 uint32_t last_=0,entered_=0,powerStable_=0,fanStarted_=0;
 uint32_t stallMs_=0,servoErrorMs_=0,pressureMs_=0,rpmErrorMs_=0;
 uint32_t serviceUntil_=0,serviceLast_=0;
 float boostCeiling_=1,returnFrom_=0,serviceFan_=0;
 uint16_t servicePulse_=1500;
 bool liveFan_=false,serviceServo_=false;
 void transition(State s,uint32_t now);
 void trip(Fault f,uint32_t now);
 void resetOutputs();
};
}
