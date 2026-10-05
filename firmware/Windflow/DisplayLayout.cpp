#include "DisplayLayout.h"
#include <stdio.h>
namespace wf {
static constexpr uint16_t background=0x0863,panel=0x10C5,white=0xFFFF,muted=0x9CF3;
static constexpr uint16_t blue=0x45DF,purple=0xB37F,yellow=0xFD87,red=0xFA8A,green=0x6EF2,track=0x2129;
static void text(Adafruit_GFX& g,int x,int y,int off,const char* s,int size,uint16_t color){
 g.setTextWrap(false);g.setTextSize(size);g.setTextColor(color);g.setCursor(x,y-off);g.print(s);
}
static void bar(Adafruit_GFX& g,int x,int y,int off,int w,int h,int percent,uint16_t color){
 g.fillRoundRect(x,y-off,w,h,3,track);
 int fill=int(lroundf(w*clamp(percent/100.f,0,1)));if(fill)g.fillRoundRect(x,y-off,fill,h,3,color);
}
void renderDisplay(Adafruit_GFX& g,const DisplayFrame& f,int16_t off,uint8_t pattern){
 g.fillScreen(background);
 if(pattern){
  if(pattern<=4){const uint16_t colors[]={0,0xF800,0x07E0,0x001F,0xFFFF};g.fillScreen(colors[pattern]);}
  else{for(int y=0;y<240;y+=20)for(int x=0;x<320;x+=20)g.fillRect(x,y-off,20,20,((x+y)/20)%2?white:track);}
  text(g,8,8,off,"SCREEN TEST / 2 SECONDS",1,pattern==4?background:white);return;
 }
 char line[64];
 bool fault=f.state==State::Fault,starting=f.state==State::Homing||f.state==State::RampUp||f.state==State::RampDown;
 bool powerShown=!fault&&(f.on||starting),boostShown=!fault&&f.mode==RotaryMode::Boost&&f.on;
 uint16_t accent=fault?red:(f.mode==RotaryMode::Boost?purple:blue);
 uint16_t statusColor=fault?red:(f.thermal||f.limited?yellow:green);
 g.fillRect(0,-off,320,kScreenStatusHeight,panel);
 text(g,10,7,off,"WINDFLOW",2,white);
 g.fillRoundRect(156,6-off,154,18,4,track);text(g,164,11,off,displaySystemName(f),1,statusColor);
 snprintf(line,sizeof(line),"FAN %u%%",powerShown?f.normalPercent:0);text(g,10,29,off,line,1,accent);
 snprintf(line,sizeof(line),"BOOST %u%%",boostShown?f.boostPercent:0);text(g,220,29,off,line,1,purple);
 bar(g,10,41,off,199,8,powerShown?f.normalPercent:0,accent);
 bar(g,220,41,off,90,8,boostShown?f.boostPercent:0,purple);
 snprintf(line,sizeof(line),"PWM %u%%  |  OUTLET %u%% OPEN",f.pwmPercent,f.nozzlePercent);text(g,10,54,off,line,1,muted);
 if(fault){
  text(g,12,78,off,displayFaultName(f.fault),2,red);
  text(g,12,115,off,"Fan and servo loads disabled.",1,white);
  text(g,12,133,off,"Check cause; short press to",1,muted);
  text(g,12,148,off,"acknowledge when safe.",1,muted);
 }else if(f.state==State::Service||f.state==State::Uncommissioned||f.state==State::WaitPower||starting){
  const char* title=f.state==State::Service?"CALIBRATION":f.state==State::Uncommissioned?"CALIBRATION NEEDED":f.state==State::WaitPower?"WAITING FOR POWER":f.state==State::Homing?"OPENING NOZZLE":"STARTING UP";
  text(g,12,78,off,title,2,white);
  if(f.state==State::Service){text(g,12,116,off,"Use the USB serial service console.",1,muted);text(g,12,135,off,"Wheel jogs servo in service only.",1,muted);}
  else if(f.state==State::Uncommissioned){text(g,12,116,off,"Fit service jumper; hold at boot.",1,muted);text(g,12,135,off,"Calibration is required before use.",1,muted);}
  else if(f.state==State::WaitPower){text(g,12,116,off,"Connect a 15V / 2A USB-C PD source.",1,muted);text(g,12,135,off,"Screen available; fan remains off.",1,muted);}
  else{text(g,12,116,off,"Opening panels, then smooth fan ramp.",1,muted);text(g,12,135,off,"Restoring saved NORMAL power.",1,muted);}
 }else{
  const char* title=!f.on?"FAN OFF":f.mode==RotaryMode::Boost?"BOOST CONTROL":f.mode==RotaryMode::BoostEntry?"TURN TO ENTER BOOST":"NORMAL POWER";
  text(g,12,78,off,title,2,f.mode==RotaryMode::BoostEntry?yellow:accent);
  // Dial pointer shows incremental wheel phase; ring tick completion shows the separate arming turn.
  const int cx=53,cy=155,r=34;
  g.drawCircle(cx,cy-off,r,track);
  for(int i=0;i<kEncoderDetentsPerRev;i++){
   float a=i*6.28318530718f/kEncoderDetentsPerRev-1.57079632679f;
   uint16_t color=f.mode!=RotaryMode::Boost&&i<f.entryDetents?yellow:muted;
   g.drawLine(cx+int(lroundf(cosf(a)*(r-4))),cy-off+int(lroundf(sinf(a)*(r-4))),cx+int(lroundf(cosf(a)*r)),cy-off+int(lroundf(sinf(a)*r)),color);
  }
  float a=f.dialDegrees*3.14159265359f/180-1.57079632679f;
  g.drawLine(cx,cy-off,cx+int(lroundf(cosf(a)*(r-7))),cy-off+int(lroundf(sinf(a)*(r-7))),blue);
  g.fillCircle(cx,cy-off,3,blue);
  snprintf(line,sizeof(line),"%u deg",f.dialDegrees);text(g,12,196,off,line,2,white);
  text(g,15,111,off,"WHEEL POSITION",1,muted);
  if(!f.on){text(g,105,117,off,"Press to start",2,white);text(g,105,147,off,"Full turn at max power",1,muted);text(g,105,163,off,"arms boost each time.",1,muted);}
  else if(f.mode==RotaryMode::Boost){
   snprintf(line,sizeof(line),"Boost %u%%",f.boostPercent);text(g,105,117,off,line,3,purple);
   snprintf(line,sizeof(line),"Outlet: %u%% open",f.nozzlePercent);text(g,105,146,off,line,1,white);
   bar(g,105,165,off,201,9,f.boostPercent,purple);
   text(g,105,184,off,f.limited?"Safety is opening nozzle.":"Turn down to zero to exit.",1,f.limited?yellow:muted);
   text(g,105,200,off,"Re-entry needs a fresh turn.",1,muted);
  }else{
   uint16_t totalDegrees=f.entryDegreesLeft+uint16_t(f.normalDetentsLeft*360/kEncoderDetentsPerRev);
   if(f.mode==RotaryMode::BoostEntry){
    snprintf(line,sizeof(line),"%u deg",totalDegrees);text(g,105,117,off,line,3,yellow);
    text(g,105,147,off,"left to boost",2,white);
   }else{
    snprintf(line,sizeof(line),"Power %u%%",f.normalPercent);text(g,105,117,off,line,3,white);
    snprintf(line,sizeof(line),"Boost in %u deg",totalDegrees);text(g,105,147,off,line,2,muted);
   }
   bar(g,105,166,off,201,9,int(f.entryDetents*100/kBoostEntryDetents),yellow);
   text(g,105,184,off,displayEntryInstruction(f),1,f.thermal||f.limited?yellow:muted);
   if(f.normalDetentsLeft){snprintf(line,sizeof(line),"%u steps to max + 1 turn",f.normalDetentsLeft);text(g,105,200,off,line,1,muted);}
   else text(g,105,200,off,"Turn DOWN to undo progress.",1,muted);
  }
 }
 g.drawFastHLine(10,215-off,300,track);
 snprintf(line,sizeof(line),"%u RPM",f.rpm);text(g,10,225,off,line,1,white);
 if(f.temperaturesValid)snprintf(line,sizeof(line),"TEMP %.1fC",f.temperatureTenths/10.f);else snprintf(line,sizeof(line),"TEMP --");
 text(g,107,225,off,line,1,f.thermal?yellow:muted);
 if(f.pressureValid)snprintf(line,sizeof(line),"AIR %.1fPa",f.pressureTenths/10.f);else snprintf(line,sizeof(line),"AIR --");
 text(g,220,225,off,line,1,muted);
}
}
