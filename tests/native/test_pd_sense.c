#define MOTOR_HOST_TEST
#define MOTOR_BOARD_PD_SENSE
#define main firmware_entry
#include "../../firmware-c/main.c"
#undef main
#include <assert.h>
#include "fake_application.h"

static void sample_stable(void) {
    for (int i = 0; i < 3; ++i) {
        fake_us += 100000;
        sample();
    }
}
int main(void) {
    safe_gpio();
    sensor_initialized = true;
    pd_voltage = 9;
    power_at = fake_us + 2000000;
    fake_pins[PD_GOOD_PIN] = 1;
    sample_stable();
    assert(!power_ready());
    fake_us = power_at;
    sample_stable();
    assert(power_ready());
    assert(pd_measured == 9.0);
    status(false);
    cJSON *frame = cJSON_Parse(output);
    assert(frame);
    assert(cJSON_IsTrue(cJSON_GetObjectItem(frame, "pd_power_good")));
    assert(cJSON_GetObjectItem(frame, "pd_voltage_measured")->valuedouble == 9.0);
    assert(strcmp(string(frame, "firmware_version"), "1.0.21") == 0);
    cJSON_Delete(frame);
    heartbeat_seen = true;
    heartbeat_us = fake_us;
    fake_motor.enabled = true;
    fake_motor.mode = CONTINUOUS;
    fake_pins[PD_GOOD_PIN] = 0;
    protect(fake_us, fake_motor);
    assert(!fake_motor.enabled);
    assert(!power_ready());
    fake_pins[PD_GOOD_PIN] = 1;
    fake_pd_registers[2] = 8000;
    sample_stable();
    assert(!power_ready());
    fake_pd_registers[2] = 7200;
    sample_stable();
    assert(power_ready());
    fake_pd_available = false;
    sample();
    assert(!pd_sensor_valid && !power_ready());
    output_length = 0;
    status(true);
    frame = cJSON_Parse(output);
    assert(cJSON_IsNull(cJSON_GetObjectItem(frame, "pd_voltage_measured")));
    cJSON_Delete(frame);
    fake_pd_available = true;
    fake_pd_registers[0] = 0x4127;
    sample();
    assert(!power_ready());
    assert(fake_pd_registers[0] == 0x4526);
    sample_stable();
    assert(power_ready());
    fake_us += 300001;
    assert(!power_ready());
    pd_voltage = 5;
    assert(!pd_alarm_active());
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 0);
    pd_voltage = 9;
    power_at = fake_us + 2000000;
    fake_pd_registers[2] = 4000; /* A 5 V-only supply cannot satisfy 9 V. */
    sample();
    assert(!pd_alarm_active());
    fake_us = power_at + 499999;
    assert(!pd_alarm_active());
    ++fake_us;
    assert(pd_alarm_active());
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 440);
    fake_us += 240000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 0);
    fake_us += 60000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 294);
    fake_us += 400000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 0);
    fake_pd_registers[2] = 7200;
    sample_stable();
    assert(!pd_alarm_active());
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 0);
    puts("PASS two-tone PD alarm, negotiation grace, 5 V standby and recovery");
    puts("PASS PD sensing, scaling, settling, POWER_GOOD loss, wrong voltage, missing sensor, reset and freshness");
}

void current_capture_init(void) {}
bool current_capture_snapshot(uint16_t raw[2]) {raw[0]=2048;raw[1]=2048;return true;}
void current_capture_read(current_frame_t *f, bool connected) {memset(f,0,sizeof(*f));}
void current_capture_drop(unsigned bins) {}
