#pragma once
// Minimal host platform for the unchanged vendor Adafruit_GFX implementation.
// No display primitives or font rendering are substituted here.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <string>
#define PROGMEM
class __FlashStringHelper;
class String {
 std::string text_;
public:
 String(const char* s=""):text_(s){}
 unsigned int length()const{return static_cast<unsigned int>(text_.length());}
 const char* c_str()const{return text_.c_str();}
};
inline void yield(){}
inline float radians(float degrees){return degrees*0.017453292519943295f;}
