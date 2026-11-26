#include "ch32fun.h"
#include "tmc2209.h"

#define UART_PIN PA3
#define BIT_US 52  // Approximately 19200 baud, 8N1.
#define REG_IFCNT 0x02
#define REG_IHOLD_IRUN 0x10

static uint8_t crc8(const uint8_t *data, unsigned length)
{
    uint8_t crc = 0;
    while (length--) {
        uint8_t byte = *data++;
        for (unsigned bit = 0; bit < 8; ++bit) {
            unsigned feedback = (crc >> 7) ^ (byte & 1);
            crc <<= 1;
            if (feedback)
                crc ^= 0x07;
            byte >>= 1;
        }
    }
    return crc;
}

static void transmit(uint8_t *frame, unsigned length)
{
    frame[length - 1] = crc8(frame, length - 1);
    funDigitalWrite(UART_PIN, 1);
    funPinMode(UART_PIN, GPIO_CFGLR_OUT_10Mhz_PP);
    Delay_Us(12 * BIT_US);
    for (unsigned i = 0; i < length; ++i) {
        funDigitalWrite(UART_PIN, 0);
        Delay_Us(BIT_US);
        for (unsigned bit = 0; bit < 8; ++bit) {
            funDigitalWrite(UART_PIN, (frame[i] >> bit) & 1);
            Delay_Us(BIT_US);
        }
        funDigitalWrite(UART_PIN, 1);
        Delay_Us(BIT_US);
    }
    funPinMode(UART_PIN, GPIO_CFGLR_IN_PUPD); // latch high selects pull-up
}

static int read_counter(uint8_t *counter)
{
    uint8_t request[] = {0x05, 0, REG_IFCNT, 0};
    uint8_t response[8] = {0};
    transmit(request, sizeof(request));
    for (unsigned i = 0; i < sizeof(response); ++i) {
        uint32_t start = SysTick->CNT;
        while (funDigitalRead(UART_PIN)) {
            if ((uint32_t)(SysTick->CNT - start) > Ticks_from_Us(1500))
                return 0;
        }
        Delay_Us(BIT_US + BIT_US / 2);
        for (unsigned bit = 0; bit < 8; ++bit) {
            if (funDigitalRead(UART_PIN))
                response[i] |= 1u << bit;
            Delay_Us(BIT_US);
        }
        if (!funDigitalRead(UART_PIN))
            return 0;
    }
    if (response[0] != 0x05 || response[1] != 0xff ||
        response[2] != REG_IFCNT || response[7] != crc8(response, 7))
        return 0;

    *counter = response[6];
    return 1;
}

int tmc2209_prepare_jog(void)
{
    uint8_t before, after;
    // ADDR=0 (MS1/MS2 grounded), IHOLD=2, IRUN=9 (10/32), IHOLDDELAY=1.
    uint8_t current[] = {0x05, 0, 0x80 | REG_IHOLD_IRUN, 0, 1, 9, 2, 0};
    if (!read_counter(&before))
        return 0;
    transmit(current, sizeof(current));
    if (!read_counter(&after))
        return 0;
    return after == (uint8_t)(before + 1);
}
