#include "Storage.h"
#include "SettingsRecord.h"
#include <LittleFS.h>
#include <stddef.h>
namespace wf {
static bool readRecord(const char* path,SettingsRecord& r){
 File f=LittleFS.open(path,"r");if(!f||f.size()!=sizeof(r))return false;
 if(f.read((uint8_t*)&r,sizeof(r))!=sizeof(r))return false;
 return decodeRecord(&r,sizeof(r),r);
}
bool Storage::load(Settings& s){
 LittleFSConfig config;config.setAutoFormat(false);LittleFS.setConfig(config);mounted_=LittleFS.begin();
 if(!mounted_)return false;SettingsRecord a{},b{};bool va=readRecord("/settings0.bin",a),vb=readRecord("/settings1.bin",b);
 if(!va&&!vb)return false;
 latest_=newestRecord(va,a,vb,b);
 const SettingsRecord& r=latest_?b:a;sequence_=r.sequence;s=r.settings;return true;
}
bool Storage::save(const Settings& s){
 if(!mounted_||!valid(s))return false;SettingsRecord r=makeRecord(s,sequence_+1);
 int next=latest_==0?1:0;const char* path=next?"/settings1.bin":"/settings0.bin";
 File f=LittleFS.open(path,"w");if(!f)return false;
 size_t n=f.write((const uint8_t*)&r,sizeof(r));f.flush();f.close();SettingsRecord checked{};
 if(n!=sizeof(r)||!readRecord(path,checked)||memcmp(&checked,&r,sizeof(r)))return false;
 sequence_=r.sequence;latest_=next;return true;
}
bool Storage::format(){LittleFS.end();mounted_=LittleFS.format()&&LittleFS.begin();latest_=-1;sequence_=0;return mounted_;}
}
