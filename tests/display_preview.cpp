#include "DisplayLayout.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
using namespace wf;
static void writePpm(const std::string& path,const uint16_t* pixels){
 FILE* f=fopen(path.c_str(),"wb");if(!f){perror(path.c_str());exit(1);}
 fprintf(f,"P6\n320 240\n255\n");
 for(int i=0;i<320*240;i++){
  uint16_t c=pixels[i];uint8_t rgb[]={uint8_t(((c>>11)&31)*255/31),uint8_t(((c>>5)&63)*255/63),uint8_t((c&31)*255/31)};
  if(fwrite(rgb,1,3,f)!=3){fclose(f);exit(1);}
 }
 if(fclose(f))exit(1);
}
int main(int argc,char** argv){
 if(argc!=2)return 2;
 const char* names[]={"normal","entry-start","entry-half","boost-half","fault"};
 int checks=0;
 for(int i=0;i<5;i++){
  DisplayFrame f;f.state=State::Live;f.on=true;f.pdReady=true;f.temperaturesValid=true;f.pressureValid=true;
  f.temperatureTenths=312;f.pressureTenths=35;f.rpm=1220;f.normalPercent=53;f.pwmPercent=63;f.normalDetentsLeft=12;
  if(i>0){f.normalPercent=100;f.pwmPercent=100;f.normalDetentsLeft=0;f.mode=RotaryMode::BoostEntry;f.entryReady=true;f.rpm=1800;}
  if(i==2){f.entryDetents=12;f.entryDegreesLeft=180;f.dialDegrees=180;}
  if(i==3){f.mode=RotaryMode::Boost;f.boostPercent=50;f.entryDegreesLeft=0;f.nozzlePercent=87;f.dialDegrees=180;}
  if(i==4){f.state=State::Fault;f.fault=Fault::Stall;f.night=true;f.pwmPercent=0;f.rpm=0;}
  GFXcanvas16 full(320,240),strip(320,kScreenRenderRows);
  if(!full.getBuffer()||!strip.getBuffer())return 1;
  renderDisplay(full,f,0,0);
  // Every pixel of the actual 16-row transport must match one full canvas.
  for(int y=0;y<240;y+=kScreenRenderRows){
   renderDisplay(strip,f,y,0);
   for(int n=0;n<320*kScreenRenderRows;n++){checks++;if(strip.getBuffer()[n]!=full.getBuffer()[y*320+n]){fprintf(stderr,"Strip mismatch %s at %d\n",names[i],y*320+n);return 1;}}
  }
  writePpm(std::string(argv[1])+"/"+names[i]+".ppm",full.getBuffer());
 }
 printf("PASS %d exact GFX strip pixel comparisons; five preview frames exported\n",checks);
 return 0;
}
