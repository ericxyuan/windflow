#pragma once
#include <stdint.h>
#include <math.h>
#include <initializer_list>
namespace wf {
constexpr uint16_t kSchema=2; // ADC isolation/dividers changed: require new calibration.
constexpr uint8_t kMainCapacity=16,kAmbientCapacity=8;
constexpr uint32_t kTickMs=10,kRampUpMs=1800,kRampDownMs=900;
constexpr float kOutletWidth=104.0f,kOutletHeight=94.0f,kPanelLength=55.0f;
constexpr float kMechanicalMaxAngle=15.0f;
namespace pin {
constexpr uint8_t encoderA=0,encoderB=1,button=2,tach=3,sda=4,scl=5;
constexpr uint8_t fanPwm=6,servoPwm=8,mainLed=10,ambientLed=11;
constexpr uint8_t fanEnable=12,servoEnable=13,ledEnable=14,guard=15;
constexpr uint8_t service=17,statusR=18,statusG=19,statusB=20;
constexpr uint8_t servoPowerGood=21,fanPowerGood=22;
constexpr uint8_t busAdc=26,servoFeedback=27,logicAdc=28;
}
inline float clamp(float x,float lo,float hi){return fminf(hi,fmaxf(lo,x));}
inline float approach(float x,float target,float step){return x+clamp(target-x,-step,step);}
inline float smooth(float x){x=clamp(x,0,1);return x*x*(3-2*x);}
struct Settings {
 uint16_t setting=400;
 uint8_t on=1,night=0,commissioned=0,encoderReverse=0;
 float boostThreshold=.75f,minAreaRatio=.75f,minPwm=.20f,maxPwm=1.0f;
 float rpmAtMax=1800.0f,pressureSoft=18.0f,pressureHard=24.0f;
 float warnC=55.0f,tripC=65.0f,pressureZero=0.0f;
 float busScale=11.1f,logicScale=2.1f;
 uint16_t servoUs[5]={1100,1200,1300,1400,1500};
 uint16_t feedback[5]={600,750,900,1050,1200};
 uint8_t mainCount=16,ambientCount=8,mainBrightness=36,ambientBrightness=12;
 uint8_t nightMain=0,nightAmbient=0;
 uint16_t reserved=0;
};
inline float maxPanelAngle(const Settings& s){return asinf(kOutletHeight*(1-s.minAreaRatio)/(2*kPanelLength))*180.0f/3.14159265359f;}
bool valid(const Settings& s);
float tableValue(const uint16_t* table,float f);
struct Mapping {float pwm=0,closure=0,areaRatio=1,angle=0;};
Mapping mapSetting(const Settings& s);
}
