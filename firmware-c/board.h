#ifndef MOTOR_BOARD_H
#define MOTOR_BOARD_H
#if defined(MOTOR_BOARD_A4988)
#include "boards/nema14-a4988/board.h"
#elif defined(MOTOR_BOARD_DRV8847)
#include "boards/nema17-drv8847/board.h"
#elif defined(MOTOR_BOARD_DRV8452)
#include "boards/nema23-drv8452-1.3.2/board.h"
#else
#include "boards/nema17-drv8825-1.0.42/board.h"
#endif
#ifndef TEMP_BUS
#define TEMP_BUS i2c1
#define TEMP_SDA 26
#define TEMP_SCL 27
#endif
#ifndef BOARD_FIRMWARE_VERSION
#define BOARD_FIRMWARE_VERSION "1.0.17"
#endif
#ifndef FULL_STEPS_PER_REVOLUTION
#define FULL_STEPS_PER_REVOLUTION 200
#endif
#endif
