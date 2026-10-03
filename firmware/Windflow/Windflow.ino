#include "Control.h"
#include "Hardware.h"
#include "Input.h"
#include "Lighting.h"
#include "Storage.h"
#include "Service.h"
#include <hardware/watchdog.h>
wf::Control controller;
wf::Hardware hardware;
wf::Input input;
wf::Lighting lighting;
wf::Storage storage;
wf::Service service;
uint32_t started=0,lastControl=0,lastSaved=0;
bool bootDecided=false,serviceRequested=false,resetFault=false;
void setup(){
 hardware.begin();input.begin();lighting.begin();Serial.begin(115200);
 started=millis();resetFault=watchdog_caused_reboot();storage.load(controller.settings);
 controller.begin(started,resetFault);watchdog_enable(1000,true);
}
void loop(){
 uint32_t now=millis();hardware.poll(now,controller.settings);wf::Events e=input.poll(now);
 hardware.in.displayReady=lighting.displayReady();
 if(!bootDecided){
  // Only a jumper already fitted at boot plus a continuous 4-second hold can enter service.
  if(now-started<150)serviceRequested=digitalRead(wf::pin::service)==LOW&&input.pressed();
  else if(!serviceRequested||!input.pressed()||digitalRead(wf::pin::service)!=LOW){bootDecided=true;}
  else if(now-started>=4000){bootDecided=true;if(!resetFault)controller.enterService(now);}
 }else{
  if(controller.state!=wf::State::Service){
   if(e.steps){
    uint16_t before=controller.settings.setting;controller.rotate(e.steps);
    // The entry turn and relative dial position are volatile UI state. Only
    // changes to the saved operating setting should schedule a flash write.
    if(controller.settings.setting!=before)controller.markChanged(now);
   }
   if(e.shortPress){if(controller.state==wf::State::Fault)controller.acknowledge(now,hardware.in);else controller.shortPress();controller.markChanged(now);}
   if(e.longPress){controller.longPress();controller.markChanged(now);}
  }else if(e.steps)controller.jogServo(e.steps*(controller.settings.encoderReverse?-5:5),now);
  if(now-lastControl>=wf::kTickMs){lastControl=now;controller.tick(now,hardware.in);}
 }
 hardware.apply(controller.out);lighting.poll(now,controller,hardware.in);
 service.poll(now,controller,hardware,lighting,storage);
 // Hardware PWM/PIO continue through bounded flash writes. Never write in a fault/ramp or while moving.
 bool stationary=abs(int(hardware.in.servoAdc)-int(controller.feedbackTarget()))<60;
 if(controller.settingsDirty&&controller.state==wf::State::Live&&stationary&&hardware.in.pd15v&&hardware.in.busV>=14.5f&&now-controller.changedAt>=8000&&now-lastSaved>=60000){
  if(storage.save(controller.settings)){controller.settingsDirty=false;lastSaved=now;}
  else lastSaved=now; // Back off instead of repeatedly writing a failing filesystem.
 }
 watchdog_update();
}
