#pragma once
#include <stdbool.h>
#include <stdint.h>
#define BLDC_MAX_PERCENT 8.0
#define BLDC_MAX_RUN_MS 1500u
#define BLDC_HEARTBEAT_MS 1000u
#define BLDC_ARM_MS 30000u
static inline bool bldc_live(uint32_t now,uint32_t last,bool seen) {
    return seen && (uint32_t)(now-last)<BLDC_HEARTBEAT_MS;
}
static inline bool bldc_settings(double percent,double duration) {
    return percent>=1.0 && percent<=BLDC_MAX_PERCENT && duration>=100 && duration<=BLDC_MAX_RUN_MS && (uint32_t)duration==duration;
}
