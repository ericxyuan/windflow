#include "Control.h"
#include <stdlib.h>
namespace wf {
static_assert(kEncoderDetentsPerRev>0&&kBoostEntryDetents>0&&kBoostControlDetents>0&&kNormalSettingStep>0,"Encoder control increments must be positive");
bool valid(const Settings& s){
 const float f[]={s.boostThreshold,s.minAreaRatio,s.minPwm,s.maxPwm,s.rpmAtMax,s.pressureSoft,s.pressureHard,s.warnC,s.tripC,s.pressureZero,s.busScale,s.logicScale};
 for(float v:f)if(!isfinite(v))return false;
 if(s.setting>1000||s.on>1||s.night>1||s.commissioned>1||s.encoderReverse>1)return false;
 if(s.boostThreshold<.60f||s.boostThreshold>.90f||s.minAreaRatio<.75f||s.minAreaRatio>.95f)return false;
 if(s.minPwm<.2f||s.minPwm>.4f||s.maxPwm<.6f||s.maxPwm>1||s.minPwm>=s.maxPwm)return false;
 if(s.rpmAtMax<1000||s.rpmAtMax>2100||s.pressureSoft<8||s.pressureHard>26||s.pressureHard<s.pressureSoft+3)return false;
 if(s.warnC<40||s.warnC>58||s.tripC<s.warnC+5||s.tripC>70||fabsf(s.pressureZero)>2)return false;
 if(s.busScale<10||s.busScale>12.2f||s.logicScale<1.9f||s.logicScale>2.3f)return false;
 if(!s.mainCount||s.mainCount>kMainCapacity||!s.ambientCount||s.ambientCount>kAmbientCapacity)return false;
 if(s.mainBrightness>80||s.ambientBrightness>60||s.nightMain>4||s.nightAmbient>4)return false;
 if(maxPanelAngle(s)>kMechanicalMaxAngle)return false;
 int du=int(s.servoUs[4])-s.servoUs[0],da=int(s.feedback[4])-s.feedback[0];
 if(abs(du)<80||abs(du)>800||abs(da)<120)return false;
 for(int i=0;i<5;i++){
  if(s.servoUs[i]<900||s.servoUs[i]>2100||s.feedback[i]<50||s.feedback[i]>3200)return false;
  if(i&&((int(s.servoUs[i])-s.servoUs[i-1])*du<=0||(int(s.feedback[i])-s.feedback[i-1])*da<=0))return false;
 }
 return true;
}
float tableValue(const uint16_t* table,float f){float x=clamp(f,0,1)*4;int i=int(x);if(i>=4)return table[4];return table[i]+(table[i+1]-float(table[i]))*(x-i);}
Mapping mapSetting(const Settings& s){
 Mapping m;if(!s.on||s.setting==0)return m;
 float u=s.setting/1000.f;
 if(u<=s.boostThreshold)m.pwm=s.minPwm+(s.maxPwm-s.minPwm)*u/s.boostThreshold;
 else{
  m.pwm=s.maxPwm;
  float boost=(u-s.boostThreshold)/(1-s.boostThreshold);
  m.areaRatio=1-boost*(1-s.minAreaRatio);
  m.angle=asinf(kOutletHeight*(1-m.areaRatio)/(2*kPanelLength))*180/3.14159265359f;
  m.closure=m.angle/maxPanelAngle(s);
 }
 return m;
}
void Control::resetOutputs(){out=Outputs{};out.servoUs=settings.servoUs[0];}
void Control::transition(State s,uint32_t now){state=s;entered_=now;servoErrorMs_=0;}
uint16_t Control::normalSettingLimit()const{
 // Invalid stored/calibration values still go through the commissioning gate;
 // do not pass NaN to integer conversion while presenting its safe UI fallback.
 return isfinite(settings.boostThreshold)?uint16_t(lroundf(clamp(settings.boostThreshold,0,1)*1000)):750;
}
RotaryMode Control::rotaryMode()const{
 if(state==State::Fault||state==State::Service)return RotaryMode::Normal;
 if(boostControl_)return RotaryMode::Boost;
 return settings.on&&settings.setting>=normalSettingLimit()?RotaryMode::BoostEntry:RotaryMode::Normal;
}
uint16_t Control::entryDetentsRemaining()const{return boostControl_?0:kBoostEntryDetents-entryDetents_;}
float Control::normalPowerFraction()const{
 uint16_t limit=normalSettingLimit();
 return limit?clamp(settings.setting/float(limit),0,1):0;
}
bool Control::boostEntryReady()const{
 return state==State::Live&&settings.on&&settings.setting>=normalSettingLimit()&&
        out.fanEnable&&out.pwm>=settings.maxPwm-.02f&&out.closure<=.001f&&servoOpenConfirmed_&&
        !out.thermal&&!out.boostLimited;
}
void Control::resetRotaryControl(){
 boostControl_=false;entryDetents_=0;boostDetents_=0;
 uint16_t limit=normalSettingLimit();
 if(settings.setting>limit){settings.setting=limit;settingsDirty=true;}
}
void Control::begin(uint32_t now,bool watchdogReset){
 state=State::WaitPower;fault=Fault::None;last_=now;entered_=now;
 powerStable_=0;stallMs_=0;servoErrorMs_=0;pressureMs_=0;rpmErrorMs_=0;
 liveFan_=false;servoOpenConfirmed_=false;encoderPosition_=0;boostCeiling_=1;resetRotaryControl();
 // Saved boost restores full NORMAL power, with the panels open. A fresh full
 // turn must explicitly authorize boost again after homing/startup completes.
 changedAt=now;resetOutputs();if(watchdogReset)trip(Fault::Watchdog,now);
}
void Control::trip(Fault f,uint32_t now){fault=f;transition(State::Fault,now);liveFan_=false;resetRotaryControl();resetOutputs();}
void Control::rotate(int detents){
 if(state==State::Service||state==State::Fault||detents==0)return;
 // Widen before direction reversal, multiplication or batching: INT_MIN and
 // very large accumulated input batches must behave like individual detents.
 int64_t steps=int64_t(detents)*(settings.encoderReverse?-1:1);
 int64_t phase=int64_t(encoderPosition_)+steps%kEncoderDetentsPerRev;
 encoderPosition_=uint16_t((phase+kEncoderDetentsPerRev)%kEncoderDetentsPerRev);
 uint16_t before=settings.setting,limit=normalSettingLimit();
 if(!settings.on){resetRotaryControl();}
 if(!boostControl_&&settings.setting>limit)settings.setting=limit;
 while(steps){
  if(boostControl_){
   if(steps>0){
    int64_t amount=steps<kBoostControlDetents-boostDetents_?steps:kBoostControlDetents-boostDetents_;
    boostDetents_+=uint16_t(amount);steps=0; // Extra travel at maximum never accumulates.
   }else{
    int64_t amount=-steps<boostDetents_?-steps:boostDetents_;
    boostDetents_-=uint16_t(amount);steps+=amount;
    if(!boostDetents_){boostControl_=false;entryDetents_=0;}
   }
   settings.setting=uint16_t(limit+lroundf((1000-limit)*boostFraction()));
   if(!boostControl_)settings.setting=limit;
   continue;
  }
  if(steps<0){
   int64_t undo=-steps<entryDetents_?-steps:entryDetents_;
   entryDetents_-=uint16_t(undo);steps+=undo;
   if(steps){
    int64_t value=int64_t(settings.setting)+steps*kNormalSettingStep;
    settings.setting=uint16_t(value>0?value:0);steps=0;
   }
  }else{
   if(settings.setting<limit){
    int64_t normalSteps=(limit-settings.setting+kNormalSettingStep-1)/kNormalSettingStep;
    int64_t amount=steps<normalSteps?steps:normalSteps;
    int64_t value=int64_t(settings.setting)+amount*kNormalSettingStep;
    settings.setting=uint16_t(value<limit?value:limit);steps-=amount;
   }
   if(!steps)break;
   if(!boostEntryReady()){entryDetents_=0;break;}
   int64_t amount=steps<kBoostEntryDetents-entryDetents_?steps:kBoostEntryDetents-entryDetents_;
   entryDetents_+=uint16_t(amount);steps-=amount;
   if(entryDetents_==kBoostEntryDetents){boostControl_=true;boostDetents_=0;entryDetents_=0;}
  }
 }
 // The arming turn and relative phase are volatile. Only an actual setting
 // change needs persistence; only a press changes whether the fan is on.
 if(settings.setting!=before)settingsDirty=true;
}
void Control::shortPress(){settings.on=!settings.on;if(!settings.on)resetRotaryControl();settingsDirty=true;}
void Control::longPress(){settings.night=!settings.night;settingsDirty=true;}
void Control::enterService(uint32_t now){resetRotaryControl();resetOutputs();serviceFan_=0;serviceServo_=false;liveFan_=false;servicePulse_=settings.commissioned?settings.servoUs[0]:1500;serviceUntil_=now;transition(State::Service,now);}
void Control::exitService(uint32_t now){resetRotaryControl();serviceFan_=0;serviceServo_=false;liveFan_=false;fault=Fault::None;resetOutputs();powerStable_=0;transition(State::WaitPower,now);}
bool Control::testFan(float duty,uint32_t now){if(state!=State::Service||!isfinite(duty)||duty<0||duty>settings.maxPwm)return false;serviceFan_=duty;serviceServo_=false;serviceUntil_=now+10000;serviceLast_=now;return true;}
bool Control::jogServo(int delta,uint32_t now){if(state!=State::Service||abs(delta)>10)return false;serviceFan_=0;serviceServo_=true;servicePulse_=(uint16_t)clamp(servicePulse_+delta,900,2100);serviceUntil_=now+800;serviceLast_=now;return true;}
bool Control::acknowledge(uint32_t now,const Inputs& in){
 if(state!=State::Fault||!in.pd15v||!isfinite(in.busV)||in.busV<14||in.busV>16||!isfinite(in.logicV)||in.logicV<4.65f||in.logicV>5.35f||!in.tempsValid||!isfinite(in.tempPower)||!isfinite(in.tempMotor)||!in.guardClosed||in.tempPower>settings.warnC-5||in.tempMotor>settings.warnC-5)return false;
 fault=Fault::None;settings.on=0;resetRotaryControl();markChanged(now);liveFan_=false;boostCeiling_=1;resetOutputs();powerStable_=0;transition(State::WaitPower,now);return true;
}
float Control::feedbackTarget()const{return tableValue(settings.feedback,out.closure);}
void Control::tick(uint32_t now,const Inputs& in){
 uint32_t elapsed=now-last_;last_=now;float dt=clamp(elapsed*.001f,0,.05f);uint32_t ms=(uint32_t)(dt*1000);
 servoOpenConfirmed_=in.servoPowerGood&&abs(int(in.servoAdc)-int(settings.feedback[0]))<60;
 bool power=in.pd15v&&isfinite(in.busV)&&in.busV>=14&&in.busV<=16&&in.logicV>=4.65f&&in.logicV<=5.35f;
 if(!settings.on)resetRotaryControl();
 // Programmatic changes (service/imported settings) cannot bypass the gesture.
 if(!boostControl_&&settings.setting>normalSettingLimit())resetRotaryControl();
 if(state==State::Fault){resetOutputs();return;}
 if(state==State::WaitPower){
  resetOutputs();
  if(!power){powerStable_=0;return;}
  powerStable_+=ms;
  if(powerStable_>=500){
   if(!valid(settings)||!settings.commissioned)transition(State::Uncommissioned,now);
   else transition(State::Homing,now);
  }
  return;
 }
 if(state==State::Uncommissioned){resetOutputs();return;}
 if(!power){trip(Fault::Power,now);return;}
 if(!in.tempsValid||!isfinite(in.tempPower)||!isfinite(in.tempMotor)){trip(Fault::TemperatureSensor,now);return;}
 if(in.tempPower>=settings.tripC||in.tempMotor>=settings.tripC){trip(Fault::Overtemperature,now);return;}
 if(!in.guardClosed){trip(Fault::Guard,now);return;}
 float hottest=fmaxf(in.tempPower,in.tempMotor);
 // 5 C hysteresis prevents repeated ramp/load oscillation.
 out.thermal=hottest>=settings.warnC||(out.thermal&&hottest>settings.warnC-5);
 out.ledEnable=!out.thermal;
 if(state==State::Service){
  bool active=int32_t(serviceUntil_-now)>0;
  out.pwm=active?serviceFan_:0;out.fanEnable=out.pwm>0;
  out.servoEnable=active&&serviceServo_;out.servoUs=servicePulse_;
  if(out.thermal||!in.pressureValid||fabsf(in.pressurePa-settings.pressureZero)>settings.pressureSoft){out.pwm=0;out.servoEnable=false;out.fanEnable=false;}
  // Tests expire without keepalive, and need temperature/pressure/guard protection.
 }else{
  Mapping m;
  if(settings.on&&settings.setting){
   if(boostControl_){
    m.pwm=settings.maxPwm;
    m.areaRatio=1-boostFraction()*(1-settings.minAreaRatio);
    m.angle=asinf(kOutletHeight*(1-m.areaRatio)/(2*kPanelLength))*180/3.14159265359f;
    m.closure=m.angle/maxPanelAngle(settings);
   }else m.pwm=settings.minPwm+(settings.maxPwm-settings.minPwm)*normalPowerFraction();
  }
  if(!boostControl_||boostDetents_==0)boostCeiling_=1;
  bool pressureBad=!in.pressureValid||!isfinite(in.pressurePa)||in.pressurePa-settings.pressureZero< -2;
  float pressure=in.pressurePa-settings.pressureZero;
  if(pressureBad||out.thermal)boostCeiling_=0;
  if(in.pressureValid&&pressure>settings.pressureSoft)boostCeiling_=fmaxf(0,fminf(boostCeiling_,out.closure)-dt*.9f);
  out.boostLimited=boostCeiling_<.999f;
  float targetClosure=fminf(m.closure,boostCeiling_);
  float targetPwm=m.pwm;
  if(pressureBad||out.thermal)targetPwm=fminf(targetPwm,.5f);
  if(in.pressureValid&&pressure>settings.pressureHard){targetClosure=0;boostCeiling_=0;targetPwm=fminf(targetPwm,.4f);pressureMs_+=ms;}
  else pressureMs_=0;
  if(pressureMs_>1200){trip(Fault::Pressure,now);return;}
  out.servoEnable=true;
  if(state==State::Homing){
   out.ledEnable=false;
   out.servoUs=settings.servoUs[0];out.closure=0;out.pwm=0;out.fanEnable=false;out.animation=0;
   bool home=abs(int(in.servoAdc)-int(settings.feedback[0]))<60&&in.servoPowerGood;
   if(now-entered_>=400&&home&&in.displayReady){
    if(settings.night||out.thermal||pressureBad||!settings.on||settings.setting==0)transition(State::Live,now);
    else transition(State::RampUp,now);
   }else if(now-entered_>1500&&!home){trip(Fault::Servo,now);return;}
   return;
  }
  if(state==State::RampUp){
   targetClosure=0;
   if(settings.night||out.thermal||pressureBad||!settings.on||settings.setting==0){transition(State::Live,now);targetPwm=fminf(targetPwm,.5f);}
   else{targetPwm=settings.maxPwm*smooth((now-entered_)/float(kRampUpMs));out.animation=targetPwm/settings.maxPwm;
    if(now-entered_>=kRampUpMs){returnFrom_=targetPwm;transition(State::RampDown,now);}}
  }else if(state==State::RampDown){
   targetClosure=0;float t=smooth((now-entered_)/float(kRampDownMs));
   targetPwm=returnFrom_+(targetPwm-returnFrom_)*t;out.animation=targetPwm/settings.maxPwm;
   if(settings.night||out.thermal||pressureBad||now-entered_>=kRampDownMs)transition(State::Live,now);
  }
  // Safety caps apply AFTER animation calculations; input off always wins.
  if(!settings.on||settings.setting==0)targetPwm=0;
  if(out.thermal||pressureBad)targetPwm=fminf(targetPwm,.5f);
  if(in.pressureValid&&pressure>settings.pressureHard)targetPwm=fminf(targetPwm,.4f);
  float rate=targetClosure<out.closure?1.2f:.35f;
  out.closure=approach(out.closure,targetClosure,rate*dt);
  out.servoUs=(uint16_t)lroundf(tableValue(settings.servoUs,out.closure));
  if(!settings.on||settings.setting==0)out.pwm=0;
  else if(state==State::RampUp||state==State::RampDown)out.pwm=targetPwm;
  else out.pwm=approach(out.pwm,targetPwm,(targetPwm<out.pwm?2.0f:1.0f)*dt);
  out.fanEnable=out.pwm>.001f;
  if(now-entered_>600&&(!in.servoPowerGood||abs(int(in.servoAdc)-int(feedbackTarget()))>90))servoErrorMs_+=ms;else servoErrorMs_=0;
  if(servoErrorMs_>650){trip(Fault::Servo,now);return;}
 }
 if(out.fanEnable&&!liveFan_)fanStarted_=now;
 liveFan_=out.fanEnable;
 if(out.fanEnable&&now-fanStarted_>300&&!in.fanPowerGood){trip(Fault::Power,now);return;}
 if(out.servoEnable&&state==State::Service&&now-serviceLast_>200&&!in.servoPowerGood){trip(Fault::Power,now);return;}
 if(out.pwm>=.3f&&now-fanStarted_>2400){
  float floor=fmaxf(250,settings.rpmAtMax*out.pwm*.30f);
  if(!isfinite(in.rpm)||in.rpm<floor)stallMs_+=ms;else stallMs_=0;
  if(stallMs_>=800){trip(Fault::Stall,now);return;}
 }else stallMs_=0;
 if(state==State::Live&&out.pwm>=settings.maxPwm-.02f&&now-fanStarted_>3500){
  if(in.rpm<settings.rpmAtMax*.70f||in.rpm>settings.rpmAtMax*1.25f)rpmErrorMs_+=ms;else rpmErrorMs_=0;
  if(rpmErrorMs_>=800){boostCeiling_=0;out.boostLimited=true;}
  if(rpmErrorMs_>=4000){trip(Fault::Stall,now);return;}
 }else rpmErrorMs_=0;
 if(!boostControl_&&!boostEntryReady())entryDetents_=0;
}
}
