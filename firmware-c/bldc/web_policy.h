#pragma once
#include <stdbool.h>
#include <stdint.h>
#define BLDC_MAX_PERCENT 100.0
#define BLDC_MAX_RUN_MS 60000u
#define BLDC_HEARTBEAT_MS 1000u
#define BLDC_ARM_MS 30000u
static inline bool bldc_live(uint32_t now,uint32_t last,bool seen) {
    return seen && (uint32_t)(now-last)<BLDC_HEARTBEAT_MS;
}
static inline bool bldc_settings(double percent,double duration) {
    return percent>=0.0 && percent<=BLDC_MAX_PERCENT && (duration==0 || (duration>=100 && duration<=BLDC_MAX_RUN_MS && (uint32_t)duration==duration));
}
static inline bool bldc_voltage_valid(unsigned v) { return v==5 || v==9 || v==15 || v==20; }
static inline bool bldc_voltage_ready(float measured,unsigned requested,bool moving) {
    float low=requested*(moving?0.90f:0.95f);
    if(low<4.65f) low=4.65f;
    return bldc_voltage_valid(requested) && measured>=low && measured<=requested*1.05f;
}
