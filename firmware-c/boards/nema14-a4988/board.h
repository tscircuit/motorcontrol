#ifndef NEMA14_A4988_BOARD_H
#define NEMA14_A4988_BOARD_H
/* AnasSarkiz/NEMA14_RP2040 1.13.2; A4988 MS1/MS2/MS3 tied high. */
#define BOARD_NAME "RP2040 / NEMA14 / A4988"
#define BOARD_ID "rp2040_a4988_nema14"
#define DRIVER_NAME "A4988"
#define BOARD_FIRMWARE_VERSION "1.0.18"
#define FULL_STEPS_PER_REVOLUTION 400
#define STEP_PIN 6
#define DIR_PIN 7
#define ARM_PIN 8 /* Active-low ENABLE_N */
#define WAKE_PIN 9
#define PD_GOOD_PIN 10 /* CH224A active-low PG */
#define VM_SENSE_PIN 28
#define DATA_PRESENT_PIN 29
#define LED_RED_PIN 25
#define LED_GREEN_PIN 2
#define LED_BLUE_PIN 3
#define BUZZER_PIN 16
#define START_BELOW_C 60
#define SHUTDOWN_C 75
#define SENSOR_LOW_C 60
#define VM_MIN_V 13.5
#define VM_MAX_V 16.5
#endif
