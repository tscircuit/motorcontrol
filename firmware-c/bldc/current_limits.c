#include "current_limits.h"
#include <math.h>
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
bool bldc_parse_current_limits(const cJSON *root,BldcCurrentLimits *out) {
    if(!cJSON_IsObject(root)||!out)return false;
    BldcCurrentLimits c;double input,align,phase,lock,vds;
    if(!number(root,"input_a",&input)||input<.05||input>8||
       !number(root,"align_a",&align)||!current_code(align,&c.align_code)||
       !number(root,"phase_a",&phase)||!current_code(phase,&c.phase_code)||
       !number(root,"lock_a",&lock)||!current_code(lock,&c.lock_code)||
       !number(root,"vds_v",&vds)||
       !boolean(root,"input_enabled",&c.input_enabled)||!boolean(root,"phase_enabled",&c.phase_enabled)||
       !boolean(root,"lock_enabled",&c.lock_enabled)||!boolean(root,"sense_ocp_enabled",&c.sense_ocp_enabled)||
       !boolean(root,"vds_ocp_enabled",&c.vds_ocp_enabled))return false;
    bool found=false;
    for(unsigned i=0;i<16;i++)if(fabs(vds-vds_values[i])<0.00001){c.vds_code=(uint8_t)i;found=true;break;}
    if(!found)return false;
    c.input_a=(float)input;*out=c;return true;
}
