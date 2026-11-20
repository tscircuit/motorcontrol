#include "ch32fun.h"
#include "fsusb.h"
#include "tmc2209.h"
#include <string.h>

#define DIR PA1
#define STANDBY PA4
#define STEP PB11
#define ENABLE_N PB12
#define JOG_PULSES 400
#define PERIOD_US 2500

static unsigned remaining;
static uint32_t next_step;
static char line[16];
static unsigned used;
static int overflow;

// A terminal that stops reading must never stall the motion loop.
static void reply(const char *message)
{
    uint8_t *buffer = USBFS_GetEPBufferIfAvailable(3);
    if (buffer) {
        size_t length = strlen(message);
        memcpy(buffer, message, length);
        USBFS_SendEndpoint(3, length);
    }
}

static void stop(void)
{
    funDigitalWrite(ENABLE_N, 1);
    funDigitalWrite(STEP, 0);
    remaining = 0;
}

static void command(void)
{
    if (!strcmp(line, "stop")) {
        stop();
        reply("stopped\r\n");
    } else if (!strcmp(line, "status")) {
        reply(remaining ? "nema8 moving\r\n" : "nema8 idle\r\n");
    } else if (!strcmp(line, "forward") || !strcmp(line, "reverse")) {
        if (remaining) {
            reply("busy\r\n");
            return;
        }
        if (!tmc2209_prepare_jog()) {
            reply("driver unavailable: check motor power and UART\r\n");
            return;
        }
        funDigitalWrite(DIR, line[0] == 'f');
        funDigitalWrite(ENABLE_N, 0);
        remaining = JOG_PULSES;
        next_step = SysTick->CNT + Ticks_from_Us(10000);
        reply("jog started\r\n");
    } else {
        reply("commands: status forward reverse stop\r\n");
    }
}

void HandleUSBInput(int count, uint8_t *data)
{
    for (int i = 0; i < count; ++i) {
        char c = data[i];
        if (c == '\r' || c == '\n') {
            if (overflow) {
                reply("invalid command\r\n");
            } else if (used) {
                line[used] = 0;
                command();
            }
            used = 0;
            overflow = 0;
        } else if (!c || used == sizeof(line) - 1) {
            overflow = 1;
        } else {
            line[used++] = c;
        }
    }
}

int main(void)
{
    SystemInit();
    funGpioInitAll();
    // Set the latch before switching ENN to output.
    stop();
    funPinMode(ENABLE_N, GPIO_CFGLR_OUT_10Mhz_PP);
    funPinMode(STEP, GPIO_CFGLR_OUT_10Mhz_PP);
    funPinMode(DIR, GPIO_CFGLR_OUT_10Mhz_PP);
    funDigitalWrite(STANDBY, 0);
    funPinMode(STANDBY, GPIO_CFGLR_OUT_10Mhz_PP);
    USBFSSetup();
    // VDD is fixed at 3.3 V. Select the full-speed D+ pull-up explicitly.
    AFIO->CTLR = (AFIO->CTLR & ~(UDP_PUE_MASK | UDM_PUE_MASK)) |
                 USB_PHY_V33 | UDP_PUE_1K5 | USB_IOEN;

    for (;;) {
        if (!USBFSCTX.USBFS_DevConfig) {
            stop();
            used = overflow = 0;
            continue;
        }
        // Take a coherent snapshot of the IRQ-owned CDC receive buffer.
        uint8_t packet[USBFS_PACKET_SIZE];
        NVIC_DisableIRQ(USB_IRQn);
        unsigned count = usb_inbuf_idx;
        memcpy(packet, usb_inputbuffer, count);
        usb_inbuf_idx = 0;
        NVIC_EnableIRQ(USB_IRQn);
        HandleUSBInput(count, packet);

        uint32_t now = SysTick->CNT;
        if (remaining && (int32_t)(now - next_step) >= 0) {
            funDigitalWrite(STEP, 1);
            Delay_Us(4);
            funDigitalWrite(STEP, 0);
            next_step = now + Ticks_from_Us(PERIOD_US);
            if (--remaining == 0)
                stop();
        }
    }
}
