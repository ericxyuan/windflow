#include "DisplayView.h"
namespace wf {
bool DisplayFrame::operator==(const DisplayFrame& b)const{
 return state==b.state&&fault==b.fault&&mode==b.mode&&dialDegrees==b.dialDegrees&&
 entryDegreesLeft==b.entryDegreesLeft&&entryDetents==b.entryDetents&&normalDetentsLeft==b.normalDetentsLeft&&
 normalPercent==b.normalPercent&&boostPercent==b.boostPercent&&nozzlePercent==b.nozzlePercent&&
 speedPercent==b.speedPercent&&rpm==b.rpm&&temperatureTenths==b.temperatureTenths&&pressureTenths==b.pressureTenths&&
 busTenths==b.busTenths&&on==b.on&&night==b.night&&entryReady==b.entryReady&&outletReady==b.outletReady&&powerReady==b.powerReady&&limited==b.limited&&thermal==b.thermal&&
 temperaturesValid==b.temperaturesValid&&pressureValid==b.pressureValid&&pdReady==b.pdReady;
}
DisplayFrame displayFrame(const Control& c,const Inputs& in){
 DisplayFrame f;
 f.state=c.state;f.fault=c.fault;f.mode=c.rotaryMode();f.on=c.settings.on;f.night=c.settings.night;
 f.dialDegrees=uint16_t(c.encoderPositionDetents()*360/kEncoderDetentsPerRev);
 f.entryDetents=c.entryDetents();f.entryReady=c.boostEntryReady();
 f.outletReady=c.outletOpenConfirmed();f.powerReady=c.out.motorEnable&&c.out.speedFraction>=c.settings.maxSpeedFraction-.02f;
 f.entryDegreesLeft=uint16_t(c.entryDetentsRemaining()*360/kEncoderDetentsPerRev);
 f.normalDetentsLeft=c.normalDetentsRemaining();
 f.normalPercent=uint16_t(lroundf(c.normalPowerFraction()*100));
 f.boostPercent=uint16_t(lroundf(c.boostFraction()*100));
 float area=1-2*kPanelLength*sinf(c.out.closure*maxPanelAngle(c.settings)*3.14159265359f/180)/kOutletHeight;
 f.nozzlePercent=isfinite(area)?uint16_t(lroundf(clamp(area,0,1)*100)):100;
 f.speedPercent=uint16_t(lroundf(clamp(c.out.speedFraction,0,1)*100));
 if(c.state==State::Homing||c.state==State::RampUp||c.state==State::RampDown)f.normalPercent=uint16_t(lroundf(clamp(c.out.animation,0,1)*100));
 f.limited=c.out.boostLimited;f.thermal=c.out.thermal;f.pdReady=in.pd15v;
 f.rpm=isfinite(in.rpm)?uint16_t(lroundf(clamp(in.rpm,0,9999)/10)*10):0;
 f.temperaturesValid=in.tempsValid&&isfinite(in.tempPower)&&isfinite(in.tempMotor);
 f.temperatureTenths=f.temperaturesValid?int16_t(lroundf(clamp(fmaxf(in.tempPower,in.tempMotor),-99,125)*10)):0;
 f.pressureValid=in.pressureValid&&isfinite(in.pressurePa);
 f.pressureTenths=f.pressureValid?int16_t(lroundf(clamp(in.pressurePa,-99,99)*10)):0;
 f.busTenths=isfinite(in.busV)?int16_t(lroundf(clamp(in.busV,0,99)*10)):0;
 return f;
}
const char* displayFaultName(Fault f){
 switch(f){
 case Fault::None:return "READY";
 case Fault::Power:return "POWER FAULT";
 case Fault::TemperatureSensor:return "TEMP SENSOR FAULT";
 case Fault::Overtemperature:return "OVER TEMPERATURE";
 case Fault::Stall:return "FAN STALL";
 case Fault::Servo:return "NOZZLE SERVO FAULT";
 case Fault::Pressure:return "AIRFLOW FAULT";
 case Fault::Guard:return "GRILLE REMOVED";
 case Fault::Watchdog:return "SYSTEM RESET FAULT";
 case Fault::EscTelemetry:return "ESC LINK FAULT";
 case Fault::EscController:return "ESC CONTROLLER FAULT";
 case Fault::Overspeed:return "ROTOR OVERSPEED";
 case Fault::MotorCurrent:return "MOTOR LOAD FAULT";
 case Fault::ReverseRotation:return "MOTOR DIRECTION FAULT";
 }
 return "SYSTEM FAULT";
}
const char* displaySystemName(const DisplayFrame& f){
 if(f.state==State::Fault)return "FAULT / LOADS OFF";
 if(f.thermal)return "TEMP / BOOST OFF";
 if(f.state==State::WaitPower)return "15V USB-C NEEDED";
 if(f.state==State::Uncommissioned)return "SETUP NEEDED";
 if(f.state==State::Service)return "CALIBRATION";
 if(f.state!=State::Live)return "STARTING";
 if(f.limited)return "BOOST LIMITED";
 if(!f.on)return "FAN OFF";
 if(f.night&&f.pdReady)return "NIGHT / USB-C READY";
 return f.pdReady?"15V USB-C READY":"CHECK POWER";
}
const char* displayEntryInstruction(const DisplayFrame& f){
 if(f.state==State::Fault)return "Clear fault before boost.";
 if(f.state==State::Service||f.state==State::Uncommissioned)return "Commission before boost.";
 if(!f.on)return "Press to start.";
 if(f.state!=State::Live)return "Wait for startup.";
 if(f.thermal||f.limited)return "Boost paused by safety.";
 if(f.normalDetentsLeft)return "Raise normal power to max.";
 if(f.entryReady)return "Turn UP to enter boost.";
 if(!f.outletReady)return "Opening outlet; wait.";
 return !f.powerReady?"Reaching full power.":"Checking boost readiness.";
}
}
