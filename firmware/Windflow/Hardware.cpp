#include "Hardware.h"
#include "SensorCodec.h"
#include <Arduino.h>
#include <hardware/i2c.h>
#include <hardware/pwm.h>
#include <hardware/clocks.h>
#include <hardware/sync.h>
namespace wf {
static volatile uint32_t tachCount=0,lastPulse=0,periodUs=0;
static void tachIrq(){uint32_t now=micros(),d=now-lastPulse;if(d>=1500){periodUs=d;lastPulse=now;tachCount++;}}
static bool tx(uint8_t a,const uint8_t* b,size_t n){return i2c_write_timeout_us(i2c0,a,b,n,false,2000)==int(n);}
static bool rx(uint8_t a,uint8_t* b,size_t n){return i2c_read_timeout_us(i2c0,a,b,n,false,2000)==int(n);}
static bool reg(uint8_t a,uint8_t r,uint8_t* b,size_t n){return i2c_write_timeout_us(i2c0,a,&r,1,true,2000)==1&&rx(a,b,n);}
static bool temperature(uint8_t addr,float& t){
 uint8_t id[2],b[2];if(!reg(addr,6,id,2)||be16(id)!=0x0054||!reg(addr,5,b,2))return false;
 t=decodeMcp(be16(b));return t>=-10&&t<=125;
}
void Hardware::begin(){
 for(uint8_t p:{pin::fanEnable,pin::servoEnable,pin::ledEnable}){pinMode(p,OUTPUT);digitalWrite(p,LOW);}
 for(uint8_t p:{pin::guard,pin::service,pin::fanPowerGood,pin::servoPowerGood})pinMode(p,INPUT_PULLUP);
 analogReadResolution(12);
 // Separate RP2040 PWM slices: GPIO6=slice3 (25kHz), GPIO8=slice4 (50Hz).
 gpio_set_function(pin::fanPwm,GPIO_FUNC_PWM);
 pwm_config fan=pwm_get_default_config();pwm_config_set_clkdiv(&fan,1.0f);
 pwm_config_set_wrap(&fan,clock_get_hz(clk_sys)/25000-1);
 pwm_init(pwm_gpio_to_slice_num(pin::fanPwm),&fan,true);
 pwm_set_gpio_level(pin::fanPwm,clock_get_hz(clk_sys)/25000); // Inverter ON = fan PWM LOW.
 gpio_set_function(pin::servoPwm,GPIO_FUNC_PWM);
 pwm_config servo=pwm_get_default_config();pwm_config_set_clkdiv(&servo,clock_get_hz(clk_sys)/1000000.0f);
 pwm_config_set_wrap(&servo,19999);pwm_init(pwm_gpio_to_slice_num(pin::servoPwm),&servo,true);
 pwm_set_gpio_level(pin::servoPwm,0);
 i2c_init(i2c0,100000);gpio_set_function(pin::sda,GPIO_FUNC_I2C);gpio_set_function(pin::scl,GPIO_FUNC_I2C);
 // External pullups are specified in the wiring document.
 pinMode(pin::tach,INPUT_PULLUP);attachInterrupt(digitalPinToInterrupt(pin::tach),tachIrq,FALLING);
}
void Hardware::poll(uint32_t now,const Settings& s){
 if(now-lastFast_>=10){lastFast_=now;
  in.busV=analogRead(pin::busAdc)*(3.3f/4095)*s.busScale;
  in.logicV=analogRead(pin::logicAdc)*(3.3f/4095)*s.logicScale;
  in.servoAdc=analogRead(pin::servoFeedback);
  in.guardClosed=digitalRead(pin::guard)==LOW;
  in.fanPowerGood=digitalRead(pin::fanPowerGood)==HIGH;
  in.servoPowerGood=digitalRead(pin::servoPowerGood)==HIGH;
  uint32_t irq=save_and_disable_interrupts();uint32_t p=periodUs,at=lastPulse,count=tachCount;restore_interrupts(irq);
  in.rpm=(count>=2&&p>0&&uint32_t(micros()-at)<600000)?30000000.0f/p:0;
 }
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
 if(now-goodPd_>250)in.pd15v=false;
}
void Hardware::apply(const Outputs& o){
 // Program signal before switching load supply on. Disable supply before dropping signal.
 if(!o.fanEnable)digitalWrite(pin::fanEnable,LOW);
 if(!o.servoEnable)digitalWrite(pin::servoEnable,LOW);
 pwm_set_gpio_level(pin::fanPwm,(uint16_t)lroundf((1-clamp(o.pwm,0,1))*(clock_get_hz(clk_sys)/25000)));
 pwm_set_gpio_level(pin::servoPwm,o.servoEnable?o.servoUs:0);
 digitalWrite(pin::fanEnable,o.fanEnable);digitalWrite(pin::servoEnable,o.servoEnable);
 digitalWrite(pin::ledEnable,o.ledEnable);
}
}
