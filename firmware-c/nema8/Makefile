.DEFAULT_GOAL := all
TARGET := nema8
TARGET_MCU := CH32X035
TARGET_MCU_PACKAGE := CH32X035F8U6
CH32FUN := vendor/ch32fun/ch32fun
ADDITIONAL_C_FILES := tmc2209.c vendor/ch32fun/extralibs/fsusb.c
EXTRA_ELF_DEPENDENCIES := funconfig.h usb_config.h tmc2209.h
include $(CH32FUN)/ch32fun.mk

.PHONY: all clean
all: $(TARGET).bin
clean: cv_clean
