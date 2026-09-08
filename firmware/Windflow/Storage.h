#pragma once
#include "Config.h"
namespace wf {
class Storage{
 bool mounted_=false;uint32_t sequence_=0;int latest_=-1;
public:
 bool load(Settings& s);
 bool save(const Settings& s);
 bool format();
 bool available()const{return mounted_;}
};
}
