#pragma once
#include <stdint.h>
#include <stddef.h>
class Print {
public:
 virtual ~Print()=default;
 virtual size_t write(uint8_t)=0;
 size_t write(const uint8_t* s,size_t n){size_t count=0;while(n--)count+=write(*s++);return count;}
 size_t print(const char* s){size_t count=0;while(*s)count+=write(uint8_t(*s++));return count;}
};
