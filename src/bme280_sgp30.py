# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import digitalio
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_sgp30

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
    time.sleep(1)
    
    elapsed_sec += 1
    if elapsed_sec > 10:
        elapsed_sec = 0
        print(
            "**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x"
            % (sgp30.baseline_eCO2, sgp30.baseline_TVOC)
        )
