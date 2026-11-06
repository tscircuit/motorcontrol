#include <assert.h>
#include "../../firmware-c/bldc/dial_policy.h"

int main(void) {
    BldcDial d;
    bldc_dial_reset(&d,0);
    assert(bldc_dial_input(&d,400,true,0,true)==DIAL_NO_CHANGE); // Held at boot.
    assert(bldc_dial_input(&d,410,false,0,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,440,false,0,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,450,true,2000,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,480,true,2000,true)==DIAL_REJECT_ZERO);
    assert(!d.armed);
    assert(bldc_dial_input(&d,800,true,0,true)==DIAL_NO_CHANGE); // Returning to zero doesn't arm.
    assert(bldc_dial_input(&d,810,false,0,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,840,false,0,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1100,true,0,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1120,true,0,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1130,true,0,true)==DIAL_ARM);
    assert(d.armed);
    assert(bldc_dial_input(&d,1140,true,3000,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1200,false,3000,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1230,false,3000,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1250,true,3000,true)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1280,true,3000,true)==DIAL_DISARM);
    bldc_dial_reset(&d,1300); // USB handoff or power loss.
    assert(bldc_dial_input(&d,1800,true,0,true)==DIAL_NO_CHANGE && !d.armed);
    assert(bldc_dial_input(&d,1810,false,0,false)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1840,false,0,false)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1850,true,0,false)==DIAL_NO_CHANGE);
    assert(bldc_dial_input(&d,1880,true,0,false)==DIAL_REJECT_NOT_READY && !d.armed);
    assert(bldc_dial_input(&d,1950,true,0,true)==DIAL_NO_CHANGE && !d.armed);
    assert(bldc_dial_percent(0)==0 && bldc_dial_percent(123)==0);
    assert(bldc_dial_percent(4095)==100);
    assert(bldc_dial_percent(2109)>49.9f && bldc_dial_percent(2109)<50.1f);
    assert(bldc_dial_slew(10,90)==10.5f);
    assert(bldc_dial_slew(90,10)==10);
    assert(bldc_dial_slew(0,0)==0);
    return 0;
}
