#pragma once
#include <stddef.h>
#include <stdint.h>
#include <math.h>
namespace wf {
// Wire format independently implemented from the public VESC protocol.
// Only GET_VALUES, SET_RPM and SET_CURRENT(0) are emitted; no config writes.
constexpr uint8_t kVescValues=4,kVescCurrent=6,kVescRpm=8;
constexpr size_t kVescMaxPayload=128;
constexpr uint32_t kVescFrameGapMs=20,kVescStaleMs=300;
inline uint16_t vescCrc(const uint8_t* b,size_t n){
 uint16_t c=0;while(n--){c^=uint16_t(*b++)<<8;for(int i=0;i<8;i++)c=(c&0x8000)?uint16_t((c<<1)^0x1021):uint16_t(c<<1);}return c;
}
inline int16_t vescI16(const uint8_t* b){return int16_t((uint16_t(b[0])<<8)|b[1]);}
inline int32_t vescI32(const uint8_t* b){return int32_t((uint32_t(b[0])<<24)|(uint32_t(b[1])<<16)|(uint32_t(b[2])<<8)|b[3]);}
inline void vescPut32(uint8_t* b,int32_t v){uint32_t u=uint32_t(v);for(int i=3;i>=0;i--){b[i]=uint8_t(u);u>>=8;}}
inline size_t vescFrame(const uint8_t* payload,size_t n,uint8_t* out,size_t capacity){
 if(!payload||!out||!n||n>kVescMaxPayload||capacity<n+5)return 0;
 out[0]=2;out[1]=uint8_t(n);for(size_t i=0;i<n;i++)out[i+2]=payload[i];
 uint16_t c=vescCrc(payload,n);out[n+2]=uint8_t(c>>8);out[n+3]=uint8_t(c);out[n+4]=3;return n+5;
}
inline size_t vescSpeedFrame(float mechanicalRpm,uint8_t polePairs,float ceiling,uint8_t* out,size_t capacity){
 if(!isfinite(mechanicalRpm)||!isfinite(ceiling)||ceiling<0||ceiling>5000||polePairs!=7||mechanicalRpm<0||mechanicalRpm>ceiling)return 0;
 uint8_t b[5]={mechanicalRpm>0?kVescRpm:kVescCurrent,0,0,0,0};
 vescPut32(b+1,int32_t(lroundf(mechanicalRpm*polePairs)));return vescFrame(b,5,out,capacity);
}
struct EscTelemetry {
 float fetC=0,motorC=0,motorA=0,inputA=0,duty=0,erpm=0,inputV=0;
 uint8_t fault=0;uint32_t receivedAt=0;bool received=false;
 bool fresh(uint32_t now)const{return received&&uint32_t(now-receivedAt)<=kVescStaleMs;}
 float mechanicalRpm()const{return erpm/7.0f;}
};
inline bool decodeVescValues(const uint8_t* b,size_t n,uint32_t now,EscTelemetry& t){
 if(!b||n<54||n>kVescMaxPayload||b[0]!=kVescValues)return false;
 EscTelemetry p;
 p.fetC=vescI16(b+1)/10.f;p.motorC=vescI16(b+3)/10.f;
 p.motorA=vescI32(b+5)/100.f;p.inputA=vescI32(b+9)/100.f;
 p.duty=vescI16(b+21)/1000.f;p.erpm=float(vescI32(b+23));p.inputV=vescI16(b+27)/10.f;p.fault=b[53];
 // Signed values remain signed: policy can detect reverse/regen instead of
 // converting dangerous telemetry into a plausible positive measurement.
 if(p.fetC< -40||p.fetC>150||p.motorC< -40||p.motorC>150||fabsf(p.motorA)>100||fabsf(p.inputA)>100||fabsf(p.duty)>1||fabsf(p.erpm)>500000||p.inputV<0||p.inputV>60)return false;
 p.received=true;p.receivedAt=now;t=p;return true;
}
class VescParser {
 uint8_t state_=0,crcHi_=0,crcLo_=0,lengthHi_=0;
 uint16_t expected_=0,used_=0;uint32_t last_=0;
 uint8_t payload_[kVescMaxPayload]{};
public:
 uint32_t rejected=0;
 void reset(){state_=0;expected_=used_=0;}
 // One bounded byte per call; accepts short/long frames up to 128 bytes.
 bool feed(uint8_t byte,uint32_t now,EscTelemetry& t){
  if(state_&&uint32_t(now-last_)>kVescFrameGapMs){reset();rejected++;}last_=now;
  switch(state_){
  case 0:if(byte==2)state_=1;else if(byte==3)state_=2;return false;
  case 1:expected_=byte;state_=4;break;
  case 2:lengthHi_=byte;state_=3;return false;
  case 3:expected_=(uint16_t(lengthHi_)<<8)|byte;state_=4;break;
  case 4:payload_[used_++]=byte;if(used_==expected_)state_=5;return false;
  case 5:crcHi_=byte;state_=6;return false;
  case 6:crcLo_=byte;state_=7;return false;
  case 7:{bool ok=byte==3&&vescCrc(payload_,expected_)==((uint16_t(crcHi_)<<8)|crcLo_);uint16_t n=expected_;reset();if(!ok){rejected++;return false;}return decodeVescValues(payload_,n,now,t);}
  }
  if(!expected_||expected_>kVescMaxPayload){reset();rejected++;}return false;
 }
};
}
