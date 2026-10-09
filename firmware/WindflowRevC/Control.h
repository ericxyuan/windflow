#pragma once
#include "Config.h"
namespace wf {
enum class State:uint8_t {WaitPower,Uncommissioned,Homing,RampUp,RampDown,Live,Service,Fault};
enum class Fault:uint8_t {None,Power,TemperatureSensor,Overtemperature,Stall,Servo,Pressure,Guard,Watchdog,EscTelemetry,EscController,Overspeed,MotorCurrent,ReverseRotation};
enum class RotaryMode:uint8_t {Normal,BoostEntry,Boost};
struct Inputs {
 // Software transport handshake, not a physical LCD health measurement.
 bool displayReady=true;
 bool pd15v=false,tempsValid=false,pressureValid=false,guardClosed=false;
 bool motorPowerGood=false,servoPowerGood=false;
 bool escTelemetryValid=false;
 uint8_t escFault=0;
 float escFetC=0,escInputA=0,escPhaseA=0,escDuty=0,escVoltage=0;
 float busV=0,logicV=0,tempPower=0,tempMotor=0,pressurePa=0,rpm=0;
 uint16_t servoAdc=0;
};
struct Outputs {
 float speedFraction=0,closure=0,animation=0;
 uint16_t servoUs=1500;
 bool motorEnable=false,escSupplyEnable=false,servoEnable=false,ledEnable=false,boostLimited=false,thermal=false;
};
Fault escSafetyFault(const Settings& s,const Inputs& in);
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
 bool testMotor(float duty,uint32_t now);
 bool jogServo(int delta,uint32_t now);
 bool acknowledge(uint32_t now,const Inputs& in);
 float feedbackTarget()const;
 // Encoder phase is relative to boot, not an absolute shaft position. Entry and
 // boost turns are deliberate runtime gestures and are never restored from flash.
 RotaryMode rotaryMode()const;
 uint16_t entryDetents()const{return entryDetents_;}
 uint16_t entryDetentsRemaining()const;
 uint16_t encoderPositionDetents()const{return encoderPosition_;}
 float encoderPositionTurns()const{return encoderPosition_/float(kEncoderDetentsPerRev);}
 uint16_t normalSettingLimit()const;
 uint16_t normalDetentsRemaining()const;
 float normalPowerFraction()const;
 float boostFraction()const{return boostDetents_/float(kBoostControlDetents);}
 bool boostEntryReady()const;
 bool outletOpenConfirmed()const{return out.closure<=.001f&&servoOpenConfirmed_;}
 bool settingsDirty=false;
 uint32_t changedAt=0;
 void markChanged(uint32_t now){settingsDirty=true;changedAt=now;}
private:
 uint32_t last_=0,entered_=0,powerStable_=0,motorStarted_=0;
 uint32_t stallMs_=0,servoErrorMs_=0,pressureMs_=0,rpmErrorMs_=0;
 uint32_t serviceUntil_=0,serviceLast_=0;
 float boostCeiling_=1,returnFrom_=0,serviceMotor_=0;
 uint16_t servicePulse_=1500;
 bool liveMotor_=false,serviceServo_=false,serviceMotorHold_=false;
 bool boostControl_=false,servoOpenConfirmed_=false,motorAtMaxConfirmed_=false;
 uint16_t entryDetents_=0,boostDetents_=0,encoderPosition_=0;
 void resetRotaryControl();
 uint16_t normalGridValue(uint16_t position)const;
 uint16_t normalGridAtOrBelow()const;
 void transition(State s,uint32_t now);
 void trip(Fault f,uint32_t now);
 void resetOutputs();
};
}
