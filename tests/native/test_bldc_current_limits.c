#include <assert.h>
#include <string.h>
#include "../../firmware-c/bldc/current_limits.h"
static const char *json="{\"input_a\":0.9,\"input_enabled\":true,\"align_a\":1,\"phase_a\":2,\"phase_enabled\":true,\"lock_a\":2.5,\"lock_enabled\":true,\"sense_ocp_enabled\":true,\"vds_ocp_enabled\":true,\"vds_v\":2}";
int main(void){
 BldcCurrentLimits c=BLDC_CURRENT_DEFAULTS;assert(bldc_gd_current_bits(&c)==0x7b);assert(bldc_fault_current_bits(&c)==0x01500000);
 cJSON *r=cJSON_Parse(json);assert(r&&bldc_parse_current_limits(r,&c));assert(c.phase_code==8&&c.align_code==4&&c.lock_code==10&&c.input_enabled);
 cJSON_ReplaceItemInObjectCaseSensitive(r,"phase_a",cJSON_CreateNumber(2.3));assert(!bldc_parse_current_limits(r,&c));
 cJSON_ReplaceItemInObjectCaseSensitive(r,"phase_a",cJSON_CreateNumber(3.75));assert(bldc_parse_current_limits(r,&c)&&c.phase_code==15);
 cJSON_ReplaceItemInObjectCaseSensitive(r,"input_a",cJSON_CreateNumber(0));assert(!bldc_parse_current_limits(r,&c));
 cJSON_ReplaceItemInObjectCaseSensitive(r,"input_a",cJSON_CreateNumber(8));assert(bldc_parse_current_limits(r,&c));
 cJSON_ReplaceItemInObjectCaseSensitive(r,"input_enabled",cJSON_CreateString("false"));assert(!bldc_parse_current_limits(r,&c));
 cJSON_ReplaceItemInObjectCaseSensitive(r,"input_enabled",cJSON_CreateBool(false));assert(bldc_parse_current_limits(r,&c)&&!c.input_enabled);
 cJSON_ReplaceItemInObjectCaseSensitive(r,"vds_v",cJSON_CreateNumber(.07));assert(!bldc_parse_current_limits(r,&c));cJSON_Delete(r);
 r=cJSON_Parse("{}");assert(!bldc_parse_current_limits(r,&c));cJSON_Delete(r);
 c.phase_enabled=false;c.lock_enabled=false;c.sense_ocp_enabled=false;c.vds_ocp_enabled=false;c.lock_code=10;c.vds_code=15;
 assert((bldc_fault_current_bits(&c)>>24)==7);assert(((bldc_fault_current_bits(&c)>>15)&15)==9);assert((bldc_gd_current_bits(&c)&0x300)==0x300);
 assert(bldc_vds_voltage(0)>.059f&&bldc_vds_voltage(15)==2);
}
