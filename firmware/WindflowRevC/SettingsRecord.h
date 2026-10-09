#pragma once
#include "Config.h"
#include "SensorCodec.h"
#include <string.h>
namespace wf {
struct SettingsRecord {uint32_t magic;uint16_t schema,size;uint32_t sequence;Settings settings;uint32_t crc;};
inline SettingsRecord makeRecord(const Settings& s,uint32_t sequence){
 SettingsRecord r{};r.magic=0x57464c57;r.schema=kSchema;r.size=sizeof(Settings);r.sequence=sequence;r.settings=s;r.crc=crc32(&r,offsetof(SettingsRecord,crc));return r;
}
inline bool decodeRecord(const void* bytes,size_t size,SettingsRecord& r){
 if(size!=sizeof(r))return false;memmove(&r,bytes,sizeof(r));
 return r.magic==0x57464c57&&r.schema==kSchema&&r.size==sizeof(Settings)&&r.crc==crc32(&r,offsetof(SettingsRecord,crc))&&valid(r.settings);
}
// Modulo comparison survives sequence rollover. Equal records choose slot 0.
inline int newestRecord(bool va,const SettingsRecord& a,bool vb,const SettingsRecord& b){
 if(!va&&!vb)return -1;return vb&&(!va||int32_t(b.sequence-a.sequence)>0)?1:0;
}
}
