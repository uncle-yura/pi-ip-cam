#!/usr/bin/python
import os
import sys
import psutil
import smbus
import time
import RPi.GPIO as GPIO

# BH1750 address
SENSOR_ADDR = 0x23
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Pi 0, CAM_GPIO1 is on GPIO 32 (CAM_GPIO0 is on GPIO 41)
# Pi 0W, CAM_GPIO1 is on GPIO 40 (CAM_GPIO0 is on GPIO 44)
# Pi3, CAM_GPIO1 is on GPIO 6 of the GPIO expander (CAM_GPIO0 is on GPIO 5),
#   accessible via the raspberrypi-exp GPIO driver)
GPIO_IR_CUT = 32
DEFAULT_THRESHOLD_VALUE = 20


def count_processes(name, file=None):
    return sum(
        name in q.name().lower()
        and (not file or (os.path.basename(file) in [os.path.basename(c) for c in q.cmdline()]))
        for q in psutil.process_iter()
    )


def check_self_running():
    if count_processes('python', __file__) > 1:
        print('already running')
        sys.exit(1)


def check_mediamtx_running():
    if count_processes('mediamtx') == 0:
        print('mediamtx not running')
        sys.exit(1)


def convert_to_number(data):
    result=(data[1] + (256 * data[0])) / 1.2
    return result


def read_sensor(bus, addr):
    data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
    return convert_to_number(data)


def main():
    check_self_running()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_IR_CUT, GPIO.OUT)

    bus = smbus.SMBus(1)

    if len(sys.argv) > 1:
        threshold = int(sys.argv[1])
    else:
        threshold = DEFAULT_THRESHOLD_VALUE

    while True:
        check_mediamtx_running()
        light_level=read_sensor(bus, SENSOR_ADDR)
        print(f"Light level: {format(light_level,'.2f')} lx, threshold: {threshold}")

        if light_level > threshold:
            GPIO.output(GPIO_IR_CUT, True)
        else:
            GPIO.output(GPIO_IR_CUT, False)

        time.sleep(1)


if __name__=="__main__":
   main()
