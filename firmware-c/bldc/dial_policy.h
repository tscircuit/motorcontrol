#pragma once
#include <stdbool.h>
#include <stdint.h>

#define BLDC_DIAL_ZERO_RAW 123u
#define BLDC_DIAL_TICK_MS 10u

typedef struct {
    bool armed, raw_down, down, zero_seen;
    uint32_t button_at, zero_at;
} BldcDial;

typedef enum { DIAL_NO_CHANGE, DIAL_ARM, DIAL_DISARM, DIAL_REJECT_NOT_READY, DIAL_REJECT_ZERO } BldcDialAction;

static inline void bldc_dial_reset(BldcDial *d, uint32_t now) {
    // A held button cannot arm at boot, after a handoff, or after power loss.
    *d=(BldcDial){.raw_down=true,.down=true,.button_at=now};
}

static inline BldcDialAction bldc_dial_input(BldcDial *d, uint32_t now, bool down, unsigned raw, bool ready) {
    if(raw>BLDC_DIAL_ZERO_RAW) d->zero_seen=false;
    else if(!d->zero_seen) {d->zero_seen=true;d->zero_at=now;}
    if(down!=d->raw_down) {d->raw_down=down;d->button_at=now;}
    if(down==d->down || (uint32_t)(now-d->button_at)<25u) return DIAL_NO_CHANGE;
    d->down=down;
    if(!down) return DIAL_NO_CHANGE;
    if(d->armed) {d->armed=false;return DIAL_DISARM;}
    if(!ready) return DIAL_REJECT_NOT_READY;
    if(!d->zero_seen || (uint32_t)(now-d->zero_at)<250u) return DIAL_REJECT_ZERO;
    d->armed=true;return DIAL_ARM;
}

static inline float bldc_dial_percent(unsigned raw) {
    if(raw<=BLDC_DIAL_ZERO_RAW) return 0;
    if(raw>=4095u) return 100;
    return (raw-BLDC_DIAL_ZERO_RAW)*(100.0f/(4095u-BLDC_DIAL_ZERO_RAW));
}

static inline float bldc_dial_slew(float current, float target) {
    // 50 percentage points per second up, immediate reduction.
    float ceiling=current+0.5f;
    return target<ceiling?target:ceiling;
}
