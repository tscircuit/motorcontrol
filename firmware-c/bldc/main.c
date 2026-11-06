// Native timed motor bring-up for package 0.3.100. PD/MCT configuration writes are RAM-only.
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/bootrom.h"
#include "hardware/adc.h"
#include "hardware/i2c.h"
#include "hardware/watchdog.h"
#include "pico/unique_id.h"
#include "cJSON.h"
#include "web_policy.h"
#include "dial_policy.h"
#include "current_limits.h"
#include "build_id.h"
#include <math.h>

static unsigned selected_voltage=9;
static BldcCurrentLimits current_limits=BLDC_CURRENT_DEFAULTS;
static bool limits_verified=false;
static bool led_error=false;
static const char *led_name="BOOT";
static void led_show(const char *name,bool red,bool green,bool blue) {
    // Common-cathode RGB: GP10=red, GP25=green, GP18=blue.
    gpio_put(10,red); gpio_put(25,green); gpio_put(18,blue); led_name=name;
}
static void led_fault(void) { led_error=true; led_show("FAULT",true,false,false); }
static void off(void) { gpio_put(2, 0); gpio_put(3, 0); }
static void low(unsigned p) { gpio_init(p); gpio_put(p, 0); gpio_set_dir(p, GPIO_OUT); }
static void release(unsigned p) { gpio_set_dir(p, GPIO_IN); }
static bool high_clock(void) {
    release(1);
    absolute_time_t limit = make_timeout_time_us(2000);
    while (!gpio_get(1)) if (time_reached(limit)) return false;
    sleep_us(5); return true;
}
static void stop(void) {
    low(1); low(0); sleep_us(5); high_clock(); release(0); sleep_us(5);
}
static bool start(void) {
    release(0); if (!high_clock() || !gpio_get(0)) return false;
    low(0); sleep_us(5); low(1); return true;
}
static bool send_byte(unsigned b) {
    for (int i = 7; i >= 0; --i) {
        if (b & (1u << i)) release(0); else low(0);
        sleep_us(5); if (!high_clock()) return false; low(1);
    }
    release(0); sleep_us(5); if (!high_clock()) return false;
    bool ack = !gpio_get(0); low(1); sleep_us(100); return ack;
}
static bool receive_byte(unsigned *b, bool last) {
    *b = 0; release(0);
    for (int i = 0; i < 8; ++i) {
        sleep_us(5); if (!high_clock()) return false;
        *b = (*b << 1) | gpio_get(0); low(1);
    }
    if (last) release(0); else low(0);
    sleep_us(5); if (!high_clock()) return false;
    low(1); release(0); sleep_us(100); return true;
}
static bool motor_read(unsigned reg, uint32_t *value) {
    bool ok = start() && send_byte(0xC0) && send_byte(0x90) && send_byte((reg>>8)&255) && send_byte(reg&255);
    if (ok) {
        ok = false;
        for (int i = 0; i < 3; ++i) if (start() && send_byte(0xC1)) { ok = true; break; }
    }
    *value = 0;
    for (int i = 0; ok && i < 4; ++i) {
        unsigned b; ok = receive_byte(&b, i == 3);
        if (ok) *value |= (uint32_t)b << (8*i);
    }
    stop(); return ok;
}
static bool motor_write(unsigned reg,uint32_t v) {
    // TI control word: write, CRC disabled, 32-bit data, little-endian payload.
    bool ok=start() && send_byte(0xc0) && send_byte(0x10) && send_byte((reg>>8)&255) && send_byte(reg&255);
    for(unsigned i=0;ok && i<4;i++) ok=send_byte((v>>(8*i))&255);
    stop(); return ok;
}
static bool patch(unsigned reg,uint32_t mask,uint32_t bits) {
    uint32_t old,check;
    if(!motor_read(reg,&old)) return false;
    uint32_t v=(old&~mask)|(bits&mask);
    if(!motor_write(reg,v) || !motor_read(reg,&check) || check!=v) return false;
    printf("Verified RAM 0x%02x=0x%08lx\n",reg,(unsigned long)v); return true;
}
static unsigned sample(unsigned channel) {
    adc_select_input(channel); (void)adc_read(); sleep_us(10); return adc_read();
}
static void led_idle(void) {
    if(led_error) { led_show("FAULT",true,false,false); return; }
    float vm=sample(1)*3.3f/4095*235/15;
    if(vm<1.0f) led_show("LOGIC_ON_MOTOR_POWER_OFF",false,false,true);
    else if(bldc_voltage_ready(vm,selected_voltage,false) && !gpio_get(6)) led_show("POWER_ON_DISARMED",true,true,false);
    else led_show("POWER_NOT_READY",true,false,false);
}
static void led_wait(void) {
    bool on=(to_ms_since_boot(get_absolute_time())/250)%2==0;
    led_show("WAITING_FOR_ARM",on,on,false);
}
static bool pd_read(unsigned reg, uint8_t *data, unsigned len) {
    uint8_t r=(uint8_t)reg;
    return i2c_write_timeout_us(i2c1,0x28,&r,1,true,10000)==1 &&
           i2c_read_timeout_us(i2c1,0x28,data,len,false,10000)==(int)len;
}
static bool pd_write(unsigned reg, uint32_t value, unsigned len) {
    uint8_t bytes[5]={(uint8_t)reg};
    for(unsigned i=0;i<len;i++) bytes[i+1]=(uint8_t)(value>>(8*i));
    return i2c_write_timeout_us(i2c1,0x28,bytes,len+1,false,10000)==(int)len+1;
}
static bool pd_value(unsigned reg,unsigned len,uint32_t *value) {
    uint8_t b[4]={0}; if(!pd_read(reg,b,len)) return false;
    *value=0; for(unsigned i=0;i<len;i++) *value|=(uint32_t)b[i]<<(8*i); return true;
}
static bool select_voltage(unsigned voltage) {
    off(); led_error=false; led_show("NEGOTIATING",false,false,true);
    if(!bldc_voltage_valid(voltage)) return false;
    uint32_t old;
    if(!pd_value(0x70,1,&old)) {led_fault();return false;}
    uint32_t motor_pdo=((voltage*20u)<<10)|200u;
    uint32_t pdo[3]={(100u<<10)|50u,motor_pdo,motor_pdo};
    bool ok=pd_write(0x70,(old&~7u)|1u,1);
    for(unsigned i=0;ok&&i<3;i++) {
        uint32_t check;
        ok=pd_write(0x85+4*i,pdo[i],4)&&pd_value(0x85+4*i,4,&check)&&check==pdo[i];
    }
    ok=ok&&pd_write(0x70,(old&~7u)|2u,1)&&pd_write(0x51,0x0d,1)&&pd_write(0x1a,0x26,1);
    if(!ok) {led_fault();return false;}
    absolute_time_t end=make_timeout_time_ms(5000);unsigned good=0;
    while(!time_reached(end)) {
        watchdog_update();off();uint32_t pe,rdo;
        float vin=sample(0)*3.3f/4095*235/15;
        bool ready=pd_value(0x29,1,&pe)&&pd_value(0x91,4,&rdo)&&pe==0x18&&
            !gpio_get(6)&&bldc_voltage_ready(vin,voltage,false)&&!(rdo&0x0c000000u)&&
            ((rdo>>10)&1023)==200&&(rdo&1023)>=200;
        good=ready?good+1:0;
        if(good>=10) {selected_voltage=voltage;return true;}
        sleep_ms(25);
    }
    led_fault();return false;
}
static void recover_pd_voltage(void) {
    static bool configured_this_attach;
    // J19 can arrive after the MCU has already booted on J1.
    float vin=sample(0)*3.3f/4095*235/15;
    if(vin<4.65f) {
        configured_this_attach=false;
        return;
    }
    if(!gpio_get(6) && bldc_voltage_ready(vin,selected_voltage,false)) return;

    uint32_t count,pdo,pe;
    if(!pd_value(0x29,1,&pe) || pe!=0x18 ||
       !pd_value(0x70,1,&count) || !pd_value(0x89,4,&pdo)) return;

    unsigned units=(pdo>>10)&1023u;
    unsigned voltage=units/20u;
    bool motor_profile=(count&7u)==2u && (pdo>>30)==0 &&
        units==voltage*20u && bldc_voltage_valid(voltage) && (pdo&1023u)==200u;
    if(!motor_profile) {
        // An unprovisioned controller can negotiate PDO3, which leaves OK2 inactive.
        if(!configured_this_attach) {
            configured_this_attach=true;
            (void)select_voltage(selected_voltage);
        }
        return;
    }

    uint32_t rdo;
    if(!gpio_get(6) && bldc_voltage_ready(vin,voltage,false) &&
       pd_value(0x91,4,&rdo) && !(rdo&0x0c000000u) &&
       ((rdo>>10)&1023u)==200u && (rdo&1023u)>=200u) {
        selected_voltage=voltage;
    }
}
static bool profile_ready=false;
static void prepare(void) {
    off(); profile_ready=false; limits_verified=false; led_error=false;
    float vm=sample(1)*3.3f/4095*235/15;
    if(!bldc_voltage_ready(vm,selected_voltage,false) || gpio_get(6)) { puts("Motor voltage or PD contract is not ready"); return; }
    bool ok=motor_write(0xe8,0x8000); // Zero digital command, override pin.
    ok=ok && patch(0xa6,0x7e,0x44); // I2C speed, hardware direction, brake disabled.
    ok=ok && patch(0xac,0x37b,bldc_gd_current_bits(&current_limits)); // Existing bidirectional CSA, now 40 V/V.
    uint32_t gd;
    ok=ok && motor_read(0xac,&gd) && (gd&(1u<<18));
    // Alignment uses 0.4 V => nominal 1 A; run/open-loop uses 0.8 V => nominal 2 A.
    ok=ok && patch(0x82,0x7fff0000u,(7u<<27)|(5u<<23)|((uint32_t)current_limits.align_code<<18)); // 10 V/s, 100 ms align, 10% cap.
    ok=ok && patch(0x84,0x7f800000u,(uint32_t)current_limits.phase_code<<23); // Open loop duty cap10%; current selected below.
    ok=ok && patch(0x88,0x6000007eu,((uint32_t)current_limits.phase_code<<2)|2u); // Open loop shares the run threshold.
    ok=ok && patch(0x92,0x0fff8078u,bldc_fault_current_bits(&current_limits)); // Configurable CBC and lock-current actions.
    ok=ok && patch(0x80,0x7e000006u,0); // Stationary start, single align; no brake/resync.
    ok=ok && patch(0x8e,3,0); // Voltage-control mode, no speed/power loop.
    ok=ok && patch(0x9a,0x60000000u,0); // Direct reference mapping.
    ok=ok && motor_write(0xe8,0x8000);
    sleep_ms(20); uint32_t cmd;
    ok=ok && motor_read(0xe4,&cmd) && (cmd&0xfffe)==0;
    profile_ready=ok; limits_verified=ok;
    if(ok) led_idle(); else led_fault();
    puts(ok?"Current profile verified in RAM; ARM OFF, digital command ZERO. No EEPROM writes.":"Profile verification failed; ARM OFF");
}

static bool running=false, armed=false, heartbeat_seen=false, browser_session=false;
static bool voltage_rearm_pending=false;
static uint32_t voltage_rearm_at;
static uint32_t heartbeat_at, arm_at, run_at, run_duration=BLDC_MAX_RUN_MS;
static unsigned baseline, edges;
static bool previous_fg;
static double percent=8;
static int direction=1;

static uint32_t driver_state, gate_fault, controller_fault;
static float electrical_hz, feed_delta,decoded_command,applied_duty,set_duty;
static const char *last_trip="None";
static const char *last_stop="None";
static float trip_voltage,trip_current,peak_current,min_voltage;
static unsigned trip_knob,trip_fault_n,trip_pd_n;
static uint32_t trip_gate,trip_controller;
static uint32_t fault_event_id,fault_event_at,fault_event_gate,fault_event_controller;
static const char *fault_event_reason="None";
static bool fault_event_stopped,fault_event_pending;
static float fault_event_voltage,fault_event_current;
static BldcCurrentLimits fault_event_limits=BLDC_CURRENT_DEFAULTS;
static uint32_t previous_limit_bits;
static bool boot_was_watchdog,dial_running;
static BldcDial dial;
static const char *dial_arm_status="No ARM press recorded";
static bool dial_reject_active;
static uint32_t dial_reject_at;
static const char *reason="Power-up: disarmed";
static char device_id[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];
static uint32_t now_ms(void) { return to_ms_since_boot(get_absolute_time()); }
static bool live(void) { return stdio_usb_connected() && bldc_live(now_ms(),heartbeat_at,heartbeat_seen); }
static bool data_usb_present(void) { return gpio_get(9) || stdio_usb_connected(); }
static bool control_available(bool local) { return local ? !data_usb_present() && dial.armed : live(); }
static bool power_ready(void) {
    float v=sample(1)*3.3f/4095*235/15;
    return bldc_voltage_ready(v,selected_voltage,false) && !gpio_get(6);
}
static void record_fault_event(const char *why,bool stopped,uint32_t gate,uint32_t controller,float voltage,float current) {
    fault_event_pending=true;fault_event_id++;fault_event_at=now_ms();fault_event_reason=why;fault_event_stopped=stopped;
    fault_event_gate=gate;fault_event_controller=controller;fault_event_voltage=voltage;fault_event_current=current;
    fault_event_limits=current_limits;
}
static void disarm(const char *why,bool fault) {
    if(running||fault)last_stop=why;
    if(fault) {
        last_trip=why;trip_voltage=sample(1)*3.3f/4095*235/15;
        trip_current=feed_delta;trip_knob=sample(3);trip_fault_n=gpio_get(4);trip_pd_n=gpio_get(6);
    }
    off(); running=false; dial_running=false; dial.armed=false; armed=false; profile_ready=false; voltage_rearm_pending=false; percent=8;
    if(fault) {
        if(!motor_read(0xe0,&trip_gate))trip_gate=0xffffffffu;
        if(!motor_read(0xe2,&trip_controller))trip_controller=0xffffffffu;
        record_fault_event(why,true,trip_gate,trip_controller,trip_voltage,trip_current);
    }
    reason=why; electrical_hz=0;
    // Only issue a zero command when the driver is powered. ARM is already low.
    if(sample(1)*3.3f/4095*235/15>4.5f) (void)motor_write(0xe8,0x8000);
    if(fault) led_fault(); else led_idle();
}
static const char *state_name(void) {
    if(led_error) return "fault";
    if(running) return driver_state==2 && electrical_hz>0 && edges>0?"running":"starting";
    if(armed||dial.armed) return "armed";
    if(voltage_rearm_pending) return "settling";
    if(sample(1)*3.3f/4095*235/15<1) return "power_off";
    return power_ready()?"idle":"power_not_ready";
}
static void telemetry(void) {
    fault_event_pending=false;
    float vin=sample(0)*3.3f/4095*235/15,vm=sample(1)*3.3f/4095*235/15;
    float current=sample(2)*3.3f/4095/0.4f;
    uint32_t elapsed=running?(uint32_t)(now_ms()-run_at):0;
    printf("{\"type\":\"telemetry\",\"protocol\":\"bldc-1\",\"firmware\":\"native-bldc\",\"firmware_version\":\"1.6.2\",\"firmware_build\":\"%s\",\"device_id\":\"%s\",\"board\":\"RP2040 / MCT8329A\",\"motor\":\"D4215-650KV\",\"state\":\"%s\",\"reason\":\"%s\",\"armed\":%s,\"motor_enabled\":%s,\"power_ready\":%s,\"pd_voltage_requested\":%u,\"pd_voltages\":[5,9,15,20],\"pd_change_while_powered\":true,\"vbus_v\":%.3f,\"vmotor_v\":%.3f,\"feed_current_a\":%.3f,\"feed_delta_a\":%.3f,\"electrical_hz\":%.1f,\"fg_edges\":%u,\"command_percent\":%.2f,\"direction\":%d,\"direction_supported\":true,\"remaining_ms\":%lu,\"led\":\"%s\",\"gate_fault\":%lu,\"controller_fault\":%lu,\"max_percent\":100,\"max_run_ms\":60000,\"continuous_supported\":true,\"phase_limit_a\":%.2f,\"heartbeat_timeout_ms\":1000,\"decoded_command_percent\":%.2f,\"applied_duty_percent\":%.2f,\"set_duty_percent\":%.2f,\"knob_raw\":%u,\"watchdog_reset\":%s,\"peak_feed_delta_a\":%.3f,\"min_run_voltage_v\":%.3f,\"last_stop_reason\":\"%s\",\"last_trip\":\"%s\",\"trip_voltage_v\":%.3f,\"trip_feed_delta_a\":%.3f,\"trip_fault_n\":%u,\"trip_pd_n\":%u,\"trip_knob_raw\":%u,\"trip_gate_fault\":%lu,\"trip_controller_fault\":%lu,\"current_limits_supported\":true,\"limits_verified\":%s,\"hardware_input_limit_a\":1.233,\"current_limits\":{\"input_a\":%.3f,\"input_enabled\":%s,\"align_a\":%.2f,\"phase_a\":%.2f,\"phase_enabled\":%s,\"lock_a\":%.2f,\"lock_enabled\":%s,\"sense_ocp_enabled\":%s,\"vds_ocp_enabled\":%s,\"vds_v\":%.2f}",
        FIRMWARE_BUILD,device_id,state_name(),reason,armed?"true":"false",running?"true":"false",power_ready()?"true":"false",selected_voltage,vin,vm,current,feed_delta,electrical_hz,edges,percent,direction,(unsigned long)(running&&elapsed<run_duration?run_duration-elapsed:0),led_name,(unsigned long)gate_fault,(unsigned long)controller_fault,current_limits.phase_code*.25,decoded_command,applied_duty,set_duty,sample(3),boot_was_watchdog?"true":"false",peak_current,min_voltage,last_stop,last_trip,trip_voltage,trip_current,trip_fault_n,trip_pd_n,trip_knob,(unsigned long)trip_gate,(unsigned long)trip_controller,limits_verified?"true":"false",current_limits.input_a,current_limits.input_enabled?"true":"false",current_limits.align_code*.25,current_limits.phase_code*.25,current_limits.phase_enabled?"true":"false",current_limits.lock_code*.25,current_limits.lock_enabled?"true":"false",current_limits.sense_ocp_enabled?"true":"false",current_limits.vds_ocp_enabled?"true":"false",bldc_vds_voltage(current_limits.vds_code));
    printf(",\"data_usb_present\":%s,\"data_vbus_present\":%s,\"dial_percent\":%.2f,\"dial_arm_status\":\"%s\",\"arm_button_down\":%s,\"uptime_ms\":%lu,\"fault_event\":{\"id\":%lu,\"at_ms\":%lu,\"reason\":\"%s\",\"stopped\":%s,\"gate\":%lu,\"controller\":%lu,\"voltage_v\":%.3f,\"current_a\":%.3f,\"input_a\":%.3f,\"align_a\":%.2f,\"phase_a\":%.2f,\"lock_a\":%.2f,\"vds_v\":%.2f}}\n",
        data_usb_present()?"true":"false",gpio_get(9)?"true":"false",bldc_dial_percent(sample(3)),dial_arm_status,gpio_get(8)?"false":"true",(unsigned long)now_ms(),(unsigned long)fault_event_id,(unsigned long)fault_event_at,fault_event_reason,fault_event_stopped?"true":"false",(unsigned long)fault_event_gate,(unsigned long)fault_event_controller,fault_event_voltage,fault_event_current,fault_event_limits.input_a,fault_event_limits.align_code*.25,fault_event_limits.phase_code*.25,fault_event_limits.lock_code*.25,bldc_vds_voltage(fault_event_limits.vds_code));

}
static void ack(int id,const char *cmd,bool ok,const char *error) {
    (void)cmd;
    printf("{\"type\":\"ack\",\"protocol\":\"bldc-1\",\"id\":%d,\"ok\":%s,\"error\":\"%s\"}\n",id,ok?"true":"false",error?error:"");
}
static bool begin_run(double speed,unsigned duration,int requested_direction,bool local) {
    if(speed==0) {disarm("Power zero",false);return true;}
    if(!armed||!profile_ready) {reason="Start rejected: not armed";return false;}
    if(!control_available(local)) {reason="Start rejected: control unavailable";return false;}
    if(!power_ready()) {reason="Start rejected: motor voltage not ready";return false;}
    if((uint32_t)(now_ms()-arm_at)>=BLDC_ARM_MS) {reason="Start rejected: arming expired";return false;}
    armed=false; baseline=sample(2);peak_current=0;min_voltage=sample(1)*3.3f/4095*235/15; edges=0; previous_fg=gpio_get(5); electrical_hz=0; driver_state=0;
    if(!patch(0xa6,0x18,requested_direction==1?0x08:0x10)) {disarm("Direction verification failed",true);return false;}
    direction=requested_direction;
    uint32_t zero,gd;
    if(!motor_read(0xe4,&zero) || (zero&0xfffe) || !motor_read(0xac,&gd) || (gd&0x40003)!=0x40003) {disarm("Zero-command or current-limit verification failed",true);return false;}
    led_show("STARTING",false,true,true); gpio_put(3,1);
    sleep_ms(20);watchdog_update();
    bool ok=motor_write(0xe6,1u<<29),released=false;
    for(unsigned i=0;ok&&i<10;i++) {
        watchdog_update();sleep_ms(10);
        ok=motor_read(0xe0,&gate_fault)&&motor_read(0xe2,&controller_fault);
        if(ok && !(gate_fault&0x9f000000u) && !(controller_fault&0xbfff0000u) && gpio_get(4)) {released=true;break;}
    }
    if(!released) {disarm("Driver enable did not clear",true);return false;}
    if(!control_available(local)) {disarm("Start cancelled: control changed",false);return false;}
    if(!motor_write(0xe8,((uint32_t)(speed*32767/100)<<16)|0x8000u)) {disarm("Speed command failed",true);return false;}
    previous_limit_bits=0;dial_running=local;running=true;percent=speed;run_duration=duration;run_at=now_ms();reason=local?"Dial control":duration?"Timed run":"Running";return true;
}
static void motion_tick(void) {
    if(!running) {
        off();
        if(voltage_rearm_pending && (uint32_t)(now_ms()-voltage_rearm_at)>=BLDC_ARM_MS) {voltage_rearm_pending=false;reason="Voltage re-arm expired";}
        if(voltage_rearm_pending && power_ready() && live()) {
            voltage_rearm_pending=false;prepare();armed=profile_ready;arm_at=now_ms();
            reason=armed?"Voltage ready; armed":"Profile verification failed";
        }
        if(armed && (!live() || !power_ready() || (uint32_t)(now_ms()-arm_at)>=BLDC_ARM_MS)) disarm("Arming expired or connection/power lost",false);
        if(armed) led_wait(); else led_idle();
        return;
    }
    if(!control_available(dial_running)) {disarm(dial_running?"Dial control ended":"Heartbeat or USB connection lost",!dial_running);return;}
    if(run_duration && (uint32_t)(now_ms()-run_at)>=run_duration) {disarm("Timed run complete",false);return;}
    float v=sample(1)*3.3f/4095*235/15;
    feed_delta=((int)sample(2)-(int)baseline)*3.3f/4095/0.4f;
    if(feed_delta>peak_current)peak_current=feed_delta;
    if(v<min_voltage)min_voltage=v;
    if(!bldc_voltage_ready(v,selected_voltage,true)) {disarm("Motor voltage out of range",true);return;}
    if(gpio_get(6)) {disarm("PD contract lost",true);return;}
    if(!gpio_get(4)) {disarm("Driver nFAULT asserted",true);return;}
    if(current_limits.input_enabled && feed_delta>current_limits.input_a) {disarm("Motor-feed current limit",true);return;}
    bool fg=gpio_get(5);if(fg!=previous_fg){edges++;previous_fg=fg;}
    static uint32_t last_driver_read;
    if((uint32_t)(now_ms()-last_driver_read)>=50) {
        last_driver_read=now_ms();uint32_t status_word;
        if(!motor_read(0xea,&status_word)) {disarm("Driver telemetry failed",true);return;}
        driver_state=status_word>>28;electrical_hz=(status_word&65535)/10.0f;
        uint32_t live_gate,live_controller;
        bool gate_ok=motor_read(0xe0,&live_gate),controller_ok=motor_read(0xe2,&live_controller);
        if(gate_ok)gate_fault=live_gate;
        if(controller_ok) {
            controller_fault=live_controller;
            uint32_t bits=live_controller&0x000c0000u;
            if(bits&~previous_limit_bits)record_fault_event("Driver current limiting",false,gate_ok?live_gate:0xffffffffu,live_controller,v,feed_delta);
            previous_limit_bits=bits;
        }

        uint32_t input_duty,current_duty,target_duty;
        if(motor_read(0x40c,&input_duty))decoded_command=input_duty*(100.0f/1073741824.0f);
        if(motor_read(0x512,&current_duty))applied_duty=current_duty*(100.0f/1073741824.0f);
        if(motor_read(0x522,&target_duty))set_duty=target_duty*(100.0f/1073741824.0f);
        if(driver_state==2&&electrical_hz>0&&edges>0) led_show("RUNNING",false,true,false);
        else led_show("STARTING",false,true,true);
    }
}
static void dial_rejected(const char *why) {
    dial_arm_status=why;dial_reject_active=true;dial_reject_at=now_ms();
}
static void dial_led(bool data) {
    if(running) return;
    if(dial_reject_active && (uint32_t)(now_ms()-dial_reject_at)<2000u) {
        led_show("DIAL_ARM_IGNORED",true,false,true);
    } else {
        dial_reject_active=false;
        if(!data && dial.armed) led_show("DIAL_READY",false,(now_ms()/250)%2==0,false);
        else if(!data && !led_error && power_ready()) led_show("DIAL_WAITING_FOR_ARM",true,true,false);
    }
}
static void dial_tick(bool data) {
    static uint32_t last_tick;
    uint32_t now=now_ms();
    if((uint32_t)(now-last_tick)<BLDC_DIAL_TICK_MS) return;
    last_tick=now;
    bool ready=!data && (running || power_ready());
    if(!ready && dial.armed) {
        disarm("Dial power lost",false);
        bldc_dial_reset(&dial,now);
    }
    unsigned raw=sample(3);
    BldcDialAction action=bldc_dial_input(&dial,now,!gpio_get(8),raw,ready);
    if(action==DIAL_REJECT_NOT_READY) dial_rejected(data?"Ignored: DATA USB connected":"Ignored: motor power or PD voltage not ready");
    if(action==DIAL_REJECT_ZERO) dial_rejected("Ignored: return dial to zero before pressing ARM");
    if(action==DIAL_DISARM) {
        dial_reject_active=false;dial_arm_status="Disarmed by ARM button";
        disarm("ARM button disarmed dial",false);return;
    }
    if(action==DIAL_ARM) {
        prepare();
        if(!profile_ready || data_usb_present()) {
            dial.armed=false;dial_rejected("Ignored: motor profile or control unavailable");return;
        }
        dial_reject_active=false;dial_arm_status="Armed: ready to turn";reason="Dial armed";
        // Re-read on the next tick; a press alone never applies motor power.
        return;
    }
    if(data || !dial.armed) return;
    float target=bldc_dial_percent(raw);
    if(target==0) {
        if(dial_running) {disarm("Dial at zero",false);dial.armed=true;}
        return;
    }
    float speed=bldc_dial_slew(running?percent:0,target);
    if(!running) {
        if(!profile_ready) prepare();
        armed=profile_ready;arm_at=now_ms();
        if(!armed || !begin_run(speed,0,1,true)) {
            if(dial.armed) disarm("Dial start failed",true);
        }
    } else if(fabs(speed-percent)>=0.25) {
        if(motor_write(0xe8,((uint32_t)(speed*32767/100)<<16)|0x8000u)) percent=speed;
        else disarm("Dial speed update failed",true);
    }
}
static void json_command(const char *line) {
    cJSON *root=cJSON_Parse(line);
    if(!root || !cJSON_IsObject(root)) {cJSON_Delete(root);return;}
    const cJSON *cmd=cJSON_GetObjectItemCaseSensitive(root,"cmd"),*id_item=cJSON_GetObjectItemCaseSensitive(root,"id");
    if(!cJSON_IsString(cmd) || !cmd->valuestring || strlen(cmd->valuestring)>24) {cJSON_Delete(root);return;}
    int id=cJSON_IsNumber(id_item)&&id_item->valuedouble>=0&&id_item->valuedouble<=2147483647?id_item->valueint:0;
    const char *name=cmd->valuestring;bool ok=true;const char *error="";
    if(!strcmp(name,"hello")) {disarm("Browser connected: disarmed",false);browser_session=true;heartbeat_seen=false;led_error=false;}
    else if(!strcmp(name,"heartbeat")) {if(browser_session){heartbeat_at=now_ms();heartbeat_seen=true;}}
    else if(!strcmp(name,"status")) {}
    else if(!strcmp(name,"stop")) {
        const cJSON *source=cJSON_GetObjectItemCaseSensitive(root,"source");
        const char *why="Stop command";
        if(cJSON_IsString(source)) {
            if(!strcmp(source->valuestring,"focus_lost"))why="Browser focus lost";
            else if(!strcmp(source->valuestring,"tab_hidden"))why="Browser tab hidden";
            else if(!strcmp(source->valuestring,"page_closed"))why="Browser page closed";
            else if(!strcmp(source->valuestring,"arrow_release"))why="Arrow released";
            else if(!strcmp(source->valuestring,"opposite_keys"))why="Opposite arrows pressed";
            else if(!strcmp(source->valuestring,"user_stop"))why="Stop button pressed";
            else if(!strcmp(source->valuestring,"voltage_change"))why="Voltage change requested";
        }
        disarm(why,false);led_error=false;
    }
    else if(!strcmp(name,"set_pd_voltage")) {
        const cJSON *v=cJSON_GetObjectItemCaseSensitive(root,"voltage");
        if(!cJSON_IsNumber(v)||v->valuedouble<0||v->valuedouble>20||v->valuedouble!=(unsigned)v->valuedouble||!bldc_voltage_valid((unsigned)v->valuedouble)) {ok=false;error="Choose 5, 9, 15 or 20 V";}
        else {disarm("Changing voltage",false);ok=select_voltage((unsigned)v->valuedouble);reason=ok?"Voltage selected; waiting to re-arm":"PD negotiation failed";voltage_rearm_pending=ok;voltage_rearm_at=now_ms();if(!ok)error="Requested PD contract unavailable";}
    }
    else if(!strcmp(name,"set_current_limits")) {
        BldcCurrentLimits proposed;
        const char *validation_error=bldc_current_limits_error(root,&proposed);
        if(validation_error) {ok=false;error=validation_error;}
        else {
            disarm("Current settings changed",false);
            BldcCurrentLimits previous=current_limits;current_limits=proposed;limits_verified=false;
            if(power_ready()) {
                prepare();ok=profile_ready;
                if(ok) {armed=live();arm_at=now_ms();reason="Current settings verified";}
                else {current_limits=previous;prepare();armed=false;reason="Current settings readback failed";error=reason;led_fault();}
            } else reason="Current settings saved for next arm";
        }
    }
    else if(!strcmp(name,"arm")) {
        if(running||!live()||!power_ready()) {ok=false;error="Need a live browser and matching motor voltage";}
        else {voltage_rearm_pending=false;prepare();ok=profile_ready;armed=ok;arm_at=now_ms();reason=ok?"Armed: waiting for browser Start":"Profile verification failed";if(!ok)error=reason;}
    }
    else if(!strcmp(name,"start") || !strcmp(name,"set_speed")) {
        const cJSON *sp=cJSON_GetObjectItemCaseSensitive(root,"percent"),*ms=cJSON_GetObjectItemCaseSensitive(root,"duration_ms"),*dir=cJSON_GetObjectItemCaseSensitive(root,"direction");
        double speed=cJSON_IsNumber(sp)?sp->valuedouble:NAN,duration=cJSON_IsNumber(ms)?ms->valuedouble:0;
        if(!bldc_settings(speed,duration) || (dir && (!cJSON_IsNumber(dir) || (dir->valuedouble!=1 && dir->valuedouble!=-1)))) {ok=false;error="Use 0-100 percent, duration 0 or 100-60000 ms, direction 1 or -1";}
        else if(!strcmp(name,"set_speed")) {
            if(!running||!live()) {ok=false;error="Motor is not running";}
            else if(speed==0) disarm("Power zero",false);
            else {ok=motor_write(0xe8,((uint32_t)(speed*32767/100)<<16)|0x8000u);if(ok)percent=speed;else disarm("Speed update failed",true);}
        } else {ok=begin_run(speed,(unsigned)duration,dir?dir->valueint:1,false);if(!ok)error=reason;}
    }
    else {ok=false;error="Unsupported BLDC command";}
    if(strcmp(name,"heartbeat")) ack(id,name,ok,error);
    cJSON_Delete(root);
    if(strcmp(line,"")==0) return;
    telemetry();
}
int main(void) {
    low(2);low(3);low(10);low(25);low(18);led_show("BOOT",false,false,true);
    for(unsigned p=0;p<=1;p++){gpio_init(p);release(p);}
    const unsigned inputs[]={4,5,6,8,9,24};
    for(unsigned i=0;i<sizeof(inputs)/sizeof(inputs[0]);i++){gpio_init(inputs[i]);gpio_set_dir(inputs[i],GPIO_IN);}
    // The 100k/100k DATA VBUS divider needs a high-impedance input.
    gpio_disable_pulls(9);
    gpio_disable_pulls(8); // SW3 already has an external pull-up.
    adc_init();for(unsigned p=26;p<=29;p++)adc_gpio_init(p);
    i2c_init(i2c1,100000);gpio_set_function(22,GPIO_FUNC_I2C);gpio_set_function(23,GPIO_FUNC_I2C);
    pico_get_unique_board_id_string(device_id,sizeof(device_id));stdio_init_all();
    boot_was_watchdog=watchdog_caused_reboot();
    watchdog_enable(250,true);
    char line[512];unsigned used=0;bool discard=false,connected=false;uint32_t last_telemetry=0;
    uint32_t last_pd_recovery=0;
    bool data=data_usb_present();
    bldc_dial_reset(&dial,now_ms());
    while(true) {
        watchdog_update();
        bool present=data_usb_present(),usb=stdio_usb_connected();
        if(present!=data) {
            disarm(present?"DATA USB connected: disarmed":"Dial mode: set zero and press ARM",false);
            bldc_dial_reset(&dial,now_ms());
            dial_reject_active=false;
            browser_session=false;heartbeat_seen=false;used=0;discard=false;
            data=present;
        }
        if(!usb && connected && data) {disarm("USB disconnected",false);browser_session=false;heartbeat_seen=false;used=0;discard=false;}
        uint32_t now=now_ms();
        if(!running && !armed && !dial.armed && !voltage_rearm_pending &&
           (uint32_t)(now-last_pd_recovery)>=250u) {
            last_pd_recovery=now;
            recover_pd_voltage();
        }
        motion_tick();
        dial_tick(data);
        dial_led(data);
        if(usb&&!connected) telemetry();
        connected=usb;
        for(unsigned n=0;n<64;n++) {
            int c=getchar_timeout_us(0);if(c==PICO_ERROR_TIMEOUT)break;
            if(c=='\r'||c=='\n') {
                if(!discard&&used){line[used]=0;if(line[0]=='{')json_command(line);else if(!strcmp(line,"boot")){disarm("Firmware update",false);reset_usb_boot(0,0);}else if(!strcmp(line,"status"))telemetry();else if(!strcmp(line,"stop"))disarm("Serial stop",false);}
                used=0;discard=false;
            } else if(c>=32&&c<127) {if(used<sizeof(line)-1&&!discard)line[used++]=(char)c;else discard=true;}
        }
        if(usb && (fault_event_pending||(uint32_t)(now_ms()-last_telemetry)>=250)){last_telemetry=now_ms();telemetry();}
        sleep_us(500);
    }
}
