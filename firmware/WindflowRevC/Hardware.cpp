#include "Hardware.h"
#include "SensorCodec.h"
#include <Arduino.h>
#include <hardware/i2c.h>
#include <hardware/pwm.h>
#include <hardware/clocks.h>
#include <hardware/sync.h>
namespace wf {
static bool tx(uint8_t a,const uint8_t* b,size_t n){return i2c_write_timeout_us(i2c0,a,b,n,false,2000)==int(n);}
static bool rx(uint8_t a,uint8_t* b,size_t n){return i2c_read_timeout_us(i2c0,a,b,n,false,2000)==int(n);}
static bool reg(uint8_t a,uint8_t r,uint8_t* b,size_t n){return i2c_write_timeout_us(i2c0,a,&r,1,true,2000)==1&&rx(a,b,n);}
static bool temperature(uint8_t addr,float& t){
 uint8_t id[2],b[2];if(!reg(addr,6,id,2)||be16(id)!=0x0054||!reg(addr,5,b,2))return false;
 t=decodeMcp(be16(b));return t>=-10&&t<=125;
}
void Hardware::begin(){
 for(uint8_t p:{pin::escEnable,pin::servoEnable,pin::ledEnable}){pinMode(p,OUTPUT);digitalWrite(p,LOW);}
 for(uint8_t p:{pin::guard,pin::service,pin::motorPowerGood,pin::servoPowerGood})pinMode(p,INPUT_PULLUP);
 analogReadResolution(12);
 // GPIO6 is an eFuse enable only. Never emit the former 25kHz fan signal.
 Serial1.setTX(pin::escTx);Serial1.setRX(pin::escRx);Serial1.begin(kEscBaud);
 gpio_set_function(pin::servoPwm,GPIO_FUNC_PWM);
 pwm_config servo=pwm_get_default_config();pwm_config_set_clkdiv(&servo,clock_get_hz(clk_sys)/1000000.0f);
 pwm_config_set_wrap(&servo,19999);pwm_init(pwm_gpio_to_slice_num(pin::servoPwm),&servo,true);
 pwm_set_gpio_level(pin::servoPwm,0);
 i2c_init(i2c0,100000);gpio_set_function(pin::sda,GPIO_FUNC_I2C);gpio_set_function(pin::scl,GPIO_FUNC_I2C);
 // External pullups are specified in the wiring document.
 pinMode(pin::opticalTach,INPUT); // Reserved optical tach; not fitted or trusted.
}
void Hardware::poll(uint32_t now,const Settings& s){
 if(now-lastFast_>=10){lastFast_=now;
  in.busV=analogRead(pin::busAdc)*(3.3f/4095)*s.busScale;
  in.logicV=analogRead(pin::logicAdc)*(3.3f/4095)*s.logicScale;
  in.servoAdc=analogRead(pin::servoFeedback);
  in.guardClosed=digitalRead(pin::guard)==LOW;
  in.motorPowerGood=digitalRead(pin::motorPowerGood)==HIGH;
  in.servoPowerGood=digitalRead(pin::servoPowerGood)==HIGH;
 }
 // Flooded/malformed UART work is bounded independently of the console.
 for(int n=0;n<64&&Serial1.available();n++)escParser_.feed(uint8_t(Serial1.read()),now,esc_);
 in.escTelemetryValid=escPowered_&&esc_.fresh(now);
 in.rpm=in.escTelemetryValid?esc_.mechanicalRpm():0;
 in.escFetC=esc_.fetC;in.escInputA=esc_.inputA;in.escPhaseA=esc_.motorA;
 in.escDuty=esc_.duty;in.escVoltage=esc_.inputV;in.escFault=esc_.fault;
 if(now-lastPd_>=100){lastPd_=now;uint8_t a,b;
  if(reg(0x08,0,&a,1)&&reg(0x08,1,&b,1)&&decodePd(a,b)){goodPd_=now;in.pd15v=true;}else in.pd15v=false;
 }
 if(now-lastTemp_>=150){lastTemp_=now;
  if(temperature(0x18,in.tempPower)&&temperature(0x19,in.tempMotor)){goodTemp_=now;in.tempsValid=true;}else in.tempsValid=false;
 }
 if(pressureState_==0&&now>=30){const uint8_t stop[]={0x3f,0xf9};tx(0x25,stop,2);pressureStart_=now;pressureState_=1;}
 else if(pressureState_==1&&now-pressureStart_>=10){const uint8_t cmd[]={0x36,0x15};
  if(tx(0x25,cmd,2)){pressureState_=2;pressureStart_=now;}else{pressureState_=0;}}
 else if(pressureState_==2&&now-pressureStart_>=25&&now-lastPressure_>=20){lastPressure_=now;uint8_t b[9];
  if(rx(0x25,b,9)&&decodePressure(b,in.pressurePa)){goodPressure_=now;in.pressureValid=true;}
  else in.pressureValid=false;
 }
 if(now-goodTemp_>400)in.tempsValid=false;
 if(now-goodPressure_>100)in.pressureValid=false;
 // A sensor supply interruption exits continuous mode. Reissue the bounded
 // stop/start sequence after stale data, instead of requiring a system reboot.
 if(pressureState_==2&&now-pressureStart_>1000&&now-goodPressure_>1000)pressureState_=0;
 if(now-goodPd_>250)in.pd15v=false;
}
static bool sendEsc(const uint8_t* payload,size_t n){
 uint8_t b[kVescMaxPayload+5];size_t length=vescFrame(payload,n,b,sizeof(b));
 if(!length||Serial1.availableForWrite()<int(length))return false;
 return Serial1.write(b,length)==length;
}
void Hardware::apply(const Outputs& o,const Settings& s,uint32_t now){
 bool supply=o.escSupplyEnable&&in.pd15v&&in.guardClosed&&in.tempsValid&&isfinite(in.tempPower)&&isfinite(in.tempMotor)&&in.tempPower<s.tripC&&in.tempMotor<s.tripC&&isfinite(in.busV)&&in.busV>=14&&in.busV<=16&&isfinite(in.logicV)&&in.logicV>=4.65f&&in.logicV<=5.35f;
 bool motion=supply&&o.motorEnable&&kMotionBuildQualified&&s.rotorQualified&&valid(s)&&in.escTelemetryValid&&escSafetyFault(s,in)==Fault::None;
 if(o.motorEnable&&!motion)supply=false;
 if(escPowered_&&!supply){esc_={};escParser_.reset();}
 digitalWrite(pin::escEnable,supply);escPowered_=supply;
 if(now-lastEscCommand_>=kEscCommandMs){
  uint8_t b[10];float rpm=motion?clamp(o.speedFraction,0,s.maxSpeedFraction)*s.rpmAtMax:0;
  size_t n=vescSpeedFrame(rpm,kMotorPolePairs,s.rpmAtMax,b,sizeof(b));
  if(n&&Serial1.availableForWrite()>=int(n)){Serial1.write(b,n);lastEscCommand_=now;}
 }
 if(supply&&now-lastEscRequest_>=kEscRequestMs){const uint8_t request=kVescValues;if(sendEsc(&request,1))lastEscRequest_=now;}
 if(!o.servoEnable)digitalWrite(pin::servoEnable,LOW);
 pwm_set_gpio_level(pin::servoPwm,o.servoEnable?o.servoUs:0);
 digitalWrite(pin::servoEnable,o.servoEnable);
 digitalWrite(pin::ledEnable,o.ledEnable);
}
}
