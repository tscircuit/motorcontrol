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
    assert(strcmp(string(frame, "firmware_version"), "1.0.22") == 0);
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
    command("{\"cmd\":\"set_pd_voltage\",\"voltage\":9}");
    fake_pd_registers[2] = 4000;
    sample();
    fake_us = power_at + 499999;
    assert(!pd_alarm_active());
    ++fake_us;
    uint64_t started = fake_us;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 440);
    fake_us = started + 300000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 294);
    fake_us = started + 2000000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 440);
    fake_us = started + 2300000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 294);
    fake_us = started + 4000000;
    indicators(fake_us, fake_motor);
    assert(!pd_alarm_active() && buzzer_frequency == 0);
    /* A fresh sample keeps the fault genuine rather than merely stale. */
    sample();
    command("{\"cmd\":\"set_pd_voltage\",\"voltage\":9}");
    fake_us = power_at + 500000;
    sample();
    indicators(fake_us, fake_motor);
    assert(pd_alarm_since == started && buzzer_frequency == 0);
    fake_pd_registers[2] = 7200;
    sample_stable();
    assert(power_ready());
    fake_pd_registers[2] = 0;
    fake_pins[PD_GOOD_PIN] = 0;
    sample();
    indicators(fake_us, fake_motor);
    assert(pd_fault_active() && !pd_alarm_active() && buzzer_frequency == 0);
    /* Only a different requested voltage gives a new notification budget. */
    command("{\"cmd\":\"set_pd_voltage\",\"voltage\":12}");
    fake_us = power_at + 500000;
    sample();
    started = fake_us;
    indicators(fake_us, fake_motor);
    assert(pd_alarm_missing && buzzer_frequency == 220);
    fake_us = started + 180000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 0);
    fake_us = started + 250000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 220);
    fake_us = started + 500000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 330);
    fake_us = started + 2000000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 220);
    fake_us = started + 2500000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 330);
    fake_us = started + 4000000;
    indicators(fake_us, fake_motor);
    assert(buzzer_frequency == 0 && !pd_alarm_active());
    assert(pd_input_missing());
    puts("PASS distinct missing-input and negotiation tones, two repetitions, same-request latch and changed-request reset");
    puts("PASS PD sensing, scaling, settling, POWER_GOOD loss, wrong voltage, missing sensor, reset and freshness");
}

void current_capture_init(void) {}
bool current_capture_snapshot(uint16_t raw[2]) {raw[0]=2048;raw[1]=2048;return true;}
void current_capture_read(current_frame_t *f, bool connected) {memset(f,0,sizeof(*f));}
void current_capture_drop(unsigned bins) {}
