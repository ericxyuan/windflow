#pragma once
#include <stdint.h>
#include <stddef.h>
namespace wf {
inline uint8_t crc8(const uint8_t* b,size_t n){uint8_t c=0xff;while(n--){c^=*b++;for(int i=0;i<8;i++)c=(c&128)?uint8_t((c<<1)^0x31):uint8_t(c<<1);}return c;}
inline uint16_t be16(const uint8_t* b){return uint16_t(b[0])<<8|b[1];}
inline bool decodePressure(const uint8_t* b,float& pa){
 if(crc8(b,2)!=b[2]||crc8(b+3,2)!=b[5]||crc8(b+6,2)!=b[8])return false;
 uint16_t scale=be16(b+6);if(scale!=240)return false; // SDP810-125Pa, reject a 500Pa part.
 pa=int16_t(be16(b))/float(scale);return pa>=-125&&pa<=125;
}
inline float decodeMcp(uint16_t raw){float t=(raw&0x0fff)/16.0f;return (raw&0x1000)?t-256:t;}
inline bool decodePd(uint8_t status0,uint8_t status1){return (status1&0x40)&&((status0>>4)==4)&&((status0&15)>=10);} // 15V, >=3A.
inline uint32_t crc32(const void* p,size_t n){uint32_t c=0xffffffffu;const uint8_t* b=(const uint8_t*)p;while(n--){c^=*b++;for(int i=0;i<8;i++)c=(c>>1)^(0xedb88320u&uint32_t(-int32_t(c&1)));}return ~c;}
}
