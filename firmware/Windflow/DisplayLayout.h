#pragma once
#include "DisplayView.h"
#include <Adafruit_GFX.h>
namespace wf {
// Draws the same layout into any GFX target. yOffset clips a page to a 16-pixel SPI strip.
// The reserved top 64 pixels carry both former light-bar functions: output and power/status.
void renderDisplay(Adafruit_GFX& canvas,const DisplayFrame& frame,int16_t yOffset=0,uint8_t testPattern=0);
}
