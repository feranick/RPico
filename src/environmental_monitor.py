# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import digitalio
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_sgp30

led1 = digitalio.DigitalInOut(board.GP13)
led1.direction = digitalio.Direction.OUTPUT
led2 = digitalio.DigitalInOut(board.GP12)
led2.direction = digitalio.Direction.OUTPUT
led3 = digitalio.DigitalInOut(board.GP11)
led3.direction = digitalio.Direction.OUTPUT
led4 = digitalio.DigitalInOut(board.GP10)
led4.direction = digitalio.Direction.OUTPUT
led5 = digitalio.DigitalInOut(board.GP9)
led5.direction = digitalio.Direction.OUTPUT

co2_l1 = 350
co2_l2 = 400
co2_l3 = 450
co2_l4 = 500
co2_l5 = 550

t_l1 = 20
t_l2 = 22
t_l3 = 24
t_l4 = 26
t_l5 = 28

# Create sensor object, using the board's default I2C bus.
# i2c = busio.I2C(board.GP1, board.GP0)  # SCL, SDA
# bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# OR create sensor object, using the board's default SPI bus.
# spi = busio.SPI(board.GP2, MISO=board.GP0, MOSI=board.GP3)
# bme_cs = digitalio.DigitalInOut(board.GP1)

spi = busio.SPI(board.GP18, MISO=board.GP16, MOSI=board.GP19)
bme_cs = digitalio.DigitalInOut(board.GP17)
bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)

i2c = busio.I2C(board.GP1, board.GP0, frequency=100000)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

# change this to match the location's pressure (hPa) at sea level
# https://w1.weather.gov/data/obhistory/KBOS.html

bme280.sea_level_pressure = 1017.3 
elapsed_sec = 0

def ledON(cd, a, b, c, d, e):
    if cd > e:
        led5.value = True
    if cd > d:
        led4.value = True
    if cd > c:
        led3.value = True
    if cd > b:
        led2.value = True
    if cd > a:
        led1.value = True

def ledOFF():
    led1.value = False
    led2.value = False
    led3.value = False
    led4.value = False
    led5.value = False

while True:
    sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)
    celsius = bme280.temperature
    RH = bme280.relative_humidity
    # sgp30.set_iaq_relative_humidity(celsius=celsius, relative_humidity=RH)
    print("\nTemperature: %0.1f C" % celsius)
    print("Humidity: %0.1f %%" % RH)
    print("Pressure: %0.1f hPa" % bme280.pressure)
    print("Altitude = %0.2f meters" % bme280.altitude)
    print("eCO2 = %d ppm \t TVOC = %d ppb" % (sgp30.eCO2, sgp30.TVOC))
    ledOFF()
    # ledON(sgp30.eCO2, co2_l1, co2_l2, co2_l3, co2_l4, co2_l5)
    ledON(celsius, t_l1, t_l2, t_l3, t_l4, t_l5)
    time.sleep(1)
    
    elapsed_sec += 1
    if elapsed_sec > 10:
        elapsed_sec = 0
        print(
            "**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x"
            % (sgp30.baseline_eCO2, sgp30.baseline_TVOC)
        )
