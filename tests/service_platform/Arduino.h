#pragma once
// USB transport only is replaced for host tests; Service.cpp and Calibration
// remain the production implementations.
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string>
struct ServiceSerial {
 std::string input,output;
 int available()const{return int(input.size());}
 int availableForWrite()const{return 4096;}
 int read(){int result=static_cast<unsigned char>(input.front());input.erase(0,1);return result;}
 void print(const char* value){output+=value;}
 void println(const char* value){output+=value;output+='\n';}
};
extern ServiceSerial Serial;
