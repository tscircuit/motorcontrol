#define MOTOR_HOST_TEST
#define MOTOR_BOARD_A4988 1
#define main firmware_entry
#include "../../firmware-c/main.c"
#undef main
#include <assert.h>
#include "fake_application.h"

static void check(const char *line, bool expected) {
    output_length = 0;
    output[0] = 0;
    command(line);
    char *last = strstr(output, "{\"type\":\"ack\"");
    assert(last);
    cJSON *frame = cJSON_Parse(last);
    assert(frame && cJSON_IsTrue(cJSON_GetObjectItem(frame, "ok")) == expected);
    cJSON_Delete(frame);
}
#define START "{\"cmd\":\"start\",\"mode\":\"steps\",\"resolution\":\"full\",\"steps\":10,\"direction\":1,\"speed_sps\":40,\"ramp_ms\":400}"
int main(int argc, char **argv) {
    for (unsigned i=0;i<32;i++) fake_pins[i]=7;
    safe_gpio();
    assert(fake_pins[ARM_PIN]==1 && fake_pins[WAKE_PIN]==0 && fake_pins[STEP_PIN]==0);
    /* Old PD selectors and driver pins are unconnected on this PCB. */
    const unsigned untouched[]={0,1,4,5,11,12,13,14,15,17,18,19,20,21,22,23,24,28,29};
    for(unsigned i=0;i<sizeof(untouched)/sizeof(*untouched);i++) assert(fake_pins[untouched[i]]==7);
    fake_pins[PD_GOOD_PIN]=0;
    sensor_initialized=true; sample();
    assert(temperature_valid && power_ready());
    check(START,false); /* Heartbeat required. */
    command("{\"cmd\":\"heartbeat\"}");
    fake_pins[PD_GOOD_PIN]=1; check(START,false);
    fake_pins[PD_GOOD_PIN]=0;
    fake_adc_values[2]=564; check(START,false); /* 5 V fallback */
    fake_adc_values[2]=2256; check(START,false); /* 20 V */
    fake_adc_values[2]=0; check(START,false);
    fake_adc_values[2]=1692;
    check(START,true);
    assert(fake_motor.target_pulses==160 && fake_motor.factor==1);
    fake_pins[PD_GOOD_PIN]=1; protect(fake_us,motor_status()); assert(!fake_motor.enabled);
    fake_pins[PD_GOOD_PIN]=0; check(START,true);
    fake_adc_values[2]=564; sample(); protect(fake_us,motor_status()); assert(!fake_motor.enabled);
    fake_adc_values[2]=1692; check(START,true);
    fake_us+=1500001; protect(fake_us,motor_status()); assert(!fake_motor.enabled);
    command("{\"cmd\":\"heartbeat\"}"); check(START,true);
    fake_connected=false; protect(fake_us,motor_status()); assert(!fake_motor.enabled);
    fake_connected=true;
    fake_registers[0]=75*256; check(START,false);
    fake_registers[0]=25*256; fake_registers[1]^=0x100; check(START,false);
    fake_registers[1]^=0x100;
    const char *unsupported[]={
      "{\"cmd\":\"set_pd_voltage\",\"voltage\":15}",
      "{\"cmd\":\"set_current_limit\",\"peak_a\":1}",
      "{\"cmd\":\"arm_power\"}",
      "{\"cmd\":\"set_current_stream_enabled\",\"enabled\":true}",
      "{\"cmd\":\"run_stall_homing\"}",
      "{\"cmd\":\"set_soft_limits\",\"enabled\":false}",
      "{\"cmd\":\"set_stall_response\",\"beeping_on\":true,\"stop_ms\":100}"};
    for(unsigned i=0;i<sizeof(unsupported)/sizeof(*unsupported);i++) check(unsupported[i],false);
    assert(fake_pins[STEP_PIN]==0 && fake_pins[ARM_PIN]==1 && fake_pins[WAKE_PIN]==0);
    check("{\"cmd\":\"set_led\",\"color\":\"cyan\"}",true);
    snprintf(device_id, sizeof(device_id), "nema14-test");
    snprintf(session, sizeof(session), "nema14-session");
    sample(); output_length=0; status(false);
    cJSON *s=cJSON_Parse(output); assert(s);
    assert(!strcmp(cJSON_GetObjectItem(s,"board_id")->valuestring,"rp2040_a4988_nema14"));
    assert(!strcmp(cJSON_GetObjectItem(s,"firmware_version")->valuestring,"1.0.19"));
    assert(cJSON_GetObjectItem(s,"steps_per_revolution")->valueint==400);
    assert(cJSON_IsNull(cJSON_GetObjectItem(s,"current_a")));
    assert(cJSON_IsFalse(cJSON_GetObjectItem(s,"current_available")));
    assert(cJSON_IsFalse(cJSON_GetObjectItem(s,"driver_fault_asserted")));
    cJSON *caps=cJSON_GetObjectItem(s,"capabilities");
    assert(cJSON_GetObjectItem(caps,"full_steps_per_revolution")->valueint==400);
    assert(cJSON_GetArraySize(cJSON_GetObjectItem(caps,"pd_voltages"))==0);
    assert(cJSON_IsFalse(cJSON_GetObjectItem(caps,"current_stream_supported")));
    assert(cJSON_IsFalse(cJSON_GetObjectItem(caps,"stall_homing_supported")));
    if(argc>1) { FILE *f=fopen(argv[1],"w"); assert(f); fputs(output,f); fclose(f); }
    cJSON_Delete(s);
    /* Disabled-driver pulse testing works without a PD supply. */
    fake_pins[PD_GOOD_PIN]=1; fake_adc_values[2]=0; sample();
    check("{\"cmd\":\"test_pulses\",\"pulses\":160,\"pulse_hz\":1000}",true);
    assert(!fake_motor.enabled);
    protect(fake_us,motor_status()); assert(fake_motor.mode==DIAGNOSTIC);
    check("{\"cmd\":\"stop\"}",true);
    puts("NEMA14 A4988 protocol and power protection tests passed");
}
