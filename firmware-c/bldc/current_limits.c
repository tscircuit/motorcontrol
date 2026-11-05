#include "current_limits.h"
#include <math.h>
#include <float.h>
static const float vds_values[]={.06f,.12f,.18f,.24f,.3f,.36f,.42f,.48f,.6f,.8f,1,1.2f,1.4f,1.6f,1.8f,2};
float bldc_vds_voltage(uint8_t code){return code<16?vds_values[code]:0;}
static bool boolean(const cJSON *r,const char *key,bool *out) {
    const cJSON *v=cJSON_GetObjectItemCaseSensitive(r,key);
    if(!cJSON_IsBool(v))return false;
    *out=cJSON_IsTrue(v);return true;
}
static bool number(const cJSON *r,const char *key,double *out) {
    const cJSON *v=cJSON_GetObjectItemCaseSensitive(r,key);
    if(!cJSON_IsNumber(v)||!isfinite(v->valuedouble))return false;
    *out=v->valuedouble;return true;
}
static bool current_code(double amps,uint8_t *out) {
    if(amps<.25||amps>3.75)return false;
    unsigned code=(unsigned)(amps*4+.5);
    if(fabs(amps-code*.25)>0.00001)return false;
    *out=(uint8_t)code;return true;
}
const char *bldc_current_limits_error(const cJSON *root,BldcCurrentLimits *out) {
    if(!cJSON_IsObject(root)||!out)return "Current settings must be an object";
    BldcCurrentLimits c;double input,align,phase,lock,vds;
    if(!number(root,"input_a",&input)||input<0||input>FLT_MAX)return "Input cutoff must be a finite nonnegative firmware number";
    if(!number(root,"align_a",&align)||!current_code(align,&c.align_code))return "Alignment current: driver supports 0.25-3.75 A in 0.25 A steps; use Ignore to disable";
    if(!number(root,"phase_a",&phase)||!current_code(phase,&c.phase_code))return "Run phase current: driver supports 0.25-3.75 A in 0.25 A steps; use Ignore to disable";
    if(!number(root,"lock_a",&lock)||!current_code(lock,&c.lock_code))return "Lock current: driver supports 0.25-3.75 A in 0.25 A steps; use Ignore to disable";
    if(!number(root,"vds_v",&vds))return "VDS threshold must be a finite number";
#define READ_BOOL(key) if(!boolean(root,#key,&c.key))return #key " must be true or false"
    READ_BOOL(input_enabled);READ_BOOL(phase_enabled);READ_BOOL(lock_enabled);READ_BOOL(sense_ocp_enabled);READ_BOOL(vds_ocp_enabled);
#undef READ_BOOL
    bool found=false;
    for(unsigned i=0;i<16;i++)if(fabs(vds-vds_values[i])<0.00001){c.vds_code=(uint8_t)i;found=true;break;}
    if(!found)return "VDS threshold is not supported by the driver; choose a dropdown value";
    c.input_a=(float)input;*out=c;return NULL;
}
bool bldc_parse_current_limits(const cJSON *root,BldcCurrentLimits *out) {return bldc_current_limits_error(root,out)==NULL;}
