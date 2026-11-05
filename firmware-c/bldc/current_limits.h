#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "cJSON.h"
typedef struct {
    float input_a;
    bool input_enabled,phase_enabled,lock_enabled,sense_ocp_enabled,vds_ocp_enabled;
    uint8_t align_code,phase_code,lock_code,vds_code;
} BldcCurrentLimits;
#define BLDC_CURRENT_DEFAULTS { .input_a=0.9f,.input_enabled=true,.phase_enabled=true,.lock_enabled=true,.sense_ocp_enabled=true,.vds_ocp_enabled=true,.align_code=4,.phase_code=8,.lock_code=10,.vds_code=15 }
bool bldc_parse_current_limits(const cJSON *root,BldcCurrentLimits *out);
float bldc_vds_voltage(uint8_t code);
static inline uint32_t bldc_gd_current_bits(const BldcCurrentLimits *c) {
    return 3u|((uint32_t)c->vds_code<<3)|(!c->sense_ocp_enabled?0x200u:0)|(!c->vds_ocp_enabled?0x100u:0);
}
static inline uint32_t bldc_fault_current_bits(const BldcCurrentLimits *c) {
    return ((uint32_t)(c->phase_enabled?1:7)<<24)|((uint32_t)c->lock_code<<19)|((uint32_t)(c->lock_enabled?0:9)<<15);
}
