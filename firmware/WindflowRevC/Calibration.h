#pragma once
#include "Control.h"
namespace wf {
// Evidence is deliberately session-only. Captures still require measuring the
// panel angle physically; an ADC value cannot prove that the linkage is correct.
class Calibration {
 uint32_t last_=0,zeroMs_=0,fanMs_=0,servoMs_=0;
 float pressureSum_=0,pressureLo_=125,pressureHi_=-125,rpmSum_=0,rpmLo_=10000,rpmHi_=0,lastDuty_=-1;
 uint16_t pressureN_=0,rpmN_=0,lastPulse_=0,adcLo_=4095,adcHi_=0;
public:
 uint8_t captures=0;
 bool zeroed=false,fanMin=false,fanMax=false;
 void reset(){*this=Calibration{};}
 bool complete()const{return captures==31&&zeroed&&fanMin&&fanMax;}
 void observe(uint32_t now,const Control& c,const Inputs& in){
  if(now-last_<50)return;
  uint32_t ms=now-last_;last_=now;if(ms>50)ms=50;
  bool healthy=c.state==State::Service&&in.pd15v&&in.tempsValid&&in.pressureValid&&in.guardClosed&&in.motorPowerGood&&in.servoPowerGood&&in.escTelemetryValid&&escSafetyFault(c.settings,in)==Fault::None&&
   isfinite(in.pressurePa)&&isfinite(in.rpm)&&!c.out.thermal;
  if(healthy&&!c.out.motorEnable&&!c.out.servoEnable&&in.rpm<60&&fabsf(in.pressurePa)<=2){
   if(pressureN_<200){zeroMs_+=ms;pressureSum_+=in.pressurePa;pressureN_++;pressureLo_=fminf(pressureLo_,in.pressurePa);pressureHi_=fmaxf(pressureHi_,in.pressurePa);}
  }else{zeroMs_=0;pressureSum_=0;pressureN_=0;pressureLo_=125;pressureHi_=-125;}
  bool openHold=abs(int(in.servoAdc)-int(c.settings.feedback[0]))<60&&c.out.servoUs==c.settings.servoUs[0];
  if(healthy&&c.out.motorEnable&&(!c.out.servoEnable||openHold)&&fabsf(c.out.speedFraction-lastDuty_)<.001f){
   if(rpmN_<200){fanMs_+=ms;if(fanMs_>=2000){rpmSum_+=in.rpm;rpmN_++;rpmLo_=fminf(rpmLo_,in.rpm);rpmHi_=fmaxf(rpmHi_,in.rpm);}}
  }else{fanMs_=0;rpmSum_=0;rpmN_=0;rpmLo_=10000;rpmHi_=0;}
  lastDuty_=c.out.speedFraction;
  if(healthy&&c.out.servoEnable&&!c.out.motorEnable&&c.out.servoUs==lastPulse_){servoMs_+=ms;adcLo_=in.servoAdc<adcLo_?in.servoAdc:adcLo_;adcHi_=in.servoAdc>adcHi_?in.servoAdc:adcHi_;}
  else{servoMs_=0;adcLo_=4095;adcHi_=0;}
  lastPulse_=c.out.servoUs;
 }
 bool capture(int i,Settings& s,const Outputs& out,const Inputs& in){
  if(i<0||i>4||!out.servoEnable||out.motorEnable||fabsf(in.rpm)>=60||servoMs_<250||adcHi_-adcLo_>12)return false;
  s.servoUs[i]=out.servoUs;s.feedback[i]=in.servoAdc;s.commissioned=0;captures|=uint8_t(1u<<i);return true;
 }
 bool zero(Settings& s){
  if(zeroMs_<1000||!pressureN_||pressureHi_-pressureLo_>.5f)return false;
  s.pressureZero=pressureSum_/pressureN_;s.commissioned=0;zeroed=true;return true;
 }
 bool measureFan(bool maximum,Settings& s){
  if(!rpmN_||fanMs_<5000||fabsf(lastDuty_-(maximum?s.maxSpeedFraction:s.minSpeedFraction))>.001f)return false;
  float rpm=rpmSum_/rpmN_;
  float target=s.rpmAtMax*lastDuty_;
  if(rpm<250||rpmHi_-rpmLo_>fmaxf(80,rpm*.10f)||fabsf(rpm-target)>target*.10f||(maximum&&(rpm<1000||rpm>kRotorAnalysisCeilingRpm)))return false;
  // The ceiling is externally qualified; measurements verify tracking and
  // never raise the ceiling to a transient measured speed.
  if(maximum)fanMax=true;else fanMin=true;
  s.commissioned=0;return true;
 }
};
}
