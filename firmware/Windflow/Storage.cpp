#include "Storage.h"
#include "SensorCodec.h"
#include <LittleFS.h>
#include <stddef.h>
namespace wf {
struct Record {uint32_t magic;uint16_t schema,size;uint32_t sequence;Settings settings;uint32_t crc;};
static bool readRecord(const char* path,Record& r){
 File f=LittleFS.open(path,"r");if(!f||f.size()!=sizeof(r))return false;
 if(f.read((uint8_t*)&r,sizeof(r))!=sizeof(r))return false;
 return r.magic==0x57464c57&&r.schema==kSchema&&r.size==sizeof(Settings)&&r.crc==crc32(&r,offsetof(Record,crc))&&valid(r.settings);
}
bool Storage::load(Settings& s){
 LittleFSConfig config;config.setAutoFormat(false);LittleFS.setConfig(config);mounted_=LittleFS.begin();
 if(!mounted_)return false;Record a{},b{};bool va=readRecord("/settings0.bin",a),vb=readRecord("/settings1.bin",b);
 if(!va&&!vb)return false;
 latest_=(vb&&(!va||int32_t(b.sequence-a.sequence)>0))?1:0;
 const Record& r=latest_?b:a;sequence_=r.sequence;s=r.settings;return true;
}
bool Storage::save(const Settings& s){
 if(!mounted_||!valid(s))return false;Record r{};r.magic=0x57464c57;r.schema=kSchema;r.size=sizeof(Settings);r.sequence=sequence_+1;r.settings=s;r.crc=crc32(&r,offsetof(Record,crc));
 int next=latest_==0?1:0;const char* path=next?"/settings1.bin":"/settings0.bin";
 File f=LittleFS.open(path,"w");if(!f)return false;
 size_t n=f.write((const uint8_t*)&r,sizeof(r));f.flush();f.close();Record checked{};
 if(n!=sizeof(r)||!readRecord(path,checked)||checked.sequence!=r.sequence)return false;
 sequence_=r.sequence;latest_=next;return true;
}
bool Storage::format(){LittleFS.end();mounted_=LittleFS.format()&&LittleFS.begin();latest_=-1;sequence_=0;return mounted_;}
}
