#pragma once
#include <Arduino.h>
#include <hardware/gpio.h>
#include <hardware/sync.h>
#include "Config.h"
#include "EncoderDecoder.h"
namespace wf {
struct Events{int steps=0;bool shortPress=false,longPress=false;};
class Input{
 EncoderDecoder decoder_;
 volatile int32_t detents_=0;
 inline static Input* self_=nullptr;
 bool raw_=false,down_=false,longSent_=false;
 uint32_t edge_=0,pressed_=0;
 static uint8_t encoderState(){
  // Read both contacts from one GPIO snapshot, avoiding a mixed two-read state.
  uint32_t levels=gpio_get_all();
  return uint8_t((((levels>>pin::encoderA)&1)<<1)|((levels>>pin::encoderB)&1));
 }
 static void encoderIrq(){
  if(self_){
   int8_t detent=self_->decoder_.transition(encoderState());
   if(detent)self_->detents_=accumulateEncoderDetent(self_->detents_,detent);
  }
 }
public:
 void begin(){
  for(uint8_t p:{pin::encoderA,pin::encoderB,pin::button})pinMode(p,INPUT_PULLUP);
  uint32_t irq=save_and_disable_interrupts();
  self_=this;decoder_.reset(encoderState());detents_=0;
  attachInterrupt(digitalPinToInterrupt(pin::encoderA),encoderIrq,CHANGE);
  attachInterrupt(digitalPinToInterrupt(pin::encoderB),encoderIrq,CHANGE);
  restore_interrupts(irq);
 }
 bool pressed()const{return down_;}
 Events poll(uint32_t now){
  Events e;
  // SPI screen transfers can occupy the main loop for milliseconds. GPIO IRQs
  // capture every completed detent meanwhile; drain/reset in a tiny critical section.
  uint32_t irq=save_and_disable_interrupts();
  e.steps=int(detents_);detents_=0;
  restore_interrupts(irq);
  bool r=digitalRead(pin::button)==LOW;if(r!=raw_){raw_=r;edge_=now;}
  if(r!=down_&&now-edge_>=25){down_=r;if(down_){pressed_=now;longSent_=false;}else if(!longSent_&&now-pressed_>=40)e.shortPress=true;}
  if(down_&&!longSent_&&now-pressed_>=1200){e.longPress=true;longSent_=true;}
  return e;
 }
};
}
