#include <assert.h>
#include <math.h>
#include "../../firmware-c/bldc/web_policy.h"
int main(void) {
 for(unsigned v=1;v<=25;v++)assert(bldc_voltage_valid(v)==(v==5||v==9||v==15||v==20));
 assert(bldc_voltage_ready(4.9f,5,false));assert(!bldc_voltage_ready(4.4f,5,true));
 assert(bldc_voltage_ready(9.1f,9,false));assert(!bldc_voltage_ready(15.0f,9,false));
 assert(bldc_voltage_ready(14.7f,15,false));assert(bldc_voltage_ready(19.8f,20,false));
 assert(!bldc_voltage_ready(NAN,9,false));

 assert(bldc_settings(8,1500));assert(bldc_settings(1,100));
 assert(!bldc_settings(NAN,1500));assert(!bldc_settings(INFINITY,1500));
 assert(bldc_settings(100,0));assert(bldc_settings(0,1500));assert(!bldc_settings(100.01,0));
 assert(bldc_settings(8,1501));assert(!bldc_settings(8,60001));assert(!bldc_settings(8,99));assert(!bldc_settings(8,100.5));
 assert(bldc_live(999,0,true));assert(!bldc_live(1000,0,true));assert(!bldc_live(10,0,false));
 assert(bldc_live(100,UINT32_MAX-200,true));assert(!bldc_live(1000,UINT32_MAX-200,true));
}
