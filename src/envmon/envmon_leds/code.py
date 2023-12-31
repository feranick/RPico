
#**********************************************
#* Environmental Monitor - Rasperry Pico
#* v2024.01.06.1
#* By: Nicola Ferralis <feranick@hotmail.com>
#**********************************************
import time
import board
import busio
import digitalio
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_sgp30

############################
# User variable definitions
############################
serial = True
time_leds_on = 3
co2eq_base = 0x958a
tvoc_base = 0x8ed3

# change this to match the location's pressure (hPa) at sea level
# https://w1.weather.gov/data/obhistory/KBOS.html
sea_level_pressure = 1020.2

co2_l1 = 400
co2_l2 = 800
co2_l3 = 1200
co2_l4 = 1600
co2_l5 = 2000

tvoc_l1 = 100
tvoc_l2 = 200
tvoc_l3 = 300
tvoc_l4 = 400
tvoc_l5 = 500

t_l1 = 18
t_l2 = 20
t_l3 = 22
t_l4 = 24
t_l5 = 26

############################
# Sensor initialization
############################
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
sgp30.set_iaq_baseline(co2eq_base, tvoc_base)
if serial:
    print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (co2eq_base, tvoc_base))

bme280.sea_level_pressure = sea_level_pressure
elapsed_sec = 0

############################
# Methods for LED control
############################
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

def led(val):
    led1.value = val
    led2.value = val
    led3.value = val
    led4.value = val
    led5.value = val
    
def led_blink(a, t):
    led(False)
    i = 0
    if a == 1:
        ld = led1
    if a == 3:
        ld = led3
    if a == 5:
        ld = led5
    while i < 2:
        ld.value = True
        time.sleep(0.5)
        ld.value = False
        time.sleep(0.5)
        i += 1
    time.sleep(t)
    led(False)

############################
# Main
############################
while True:
    # sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)
    celsius = bme280.temperature
    RH = bme280.relative_humidity
    sgp30.set_iaq_relative_humidity(celsius=celsius, relative_humidity=RH)
    if serial:
        print("\n Temperature: %0.1f C" % celsius)
        print(" Humidity: %0.1f %%" % RH)
        print(" Pressure: %0.1f hPa" % bme280.pressure)
        print(" Altitude = %0.2f meters" % bme280.altitude)
        print(" eCO2 = %d ppm" % sgp30.eCO2)
        print(" TVOC = %d ppb" % sgp30.TVOC)
        #print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (sgp30.baseline_eCO2, sgp30.baseline_TVOC))
    led(False)
    ledON(celsius, t_l1, t_l2, t_l3, t_l4, t_l5)
    time.sleep(time_leds_on)
    led_blink(1,0.5)
    led(False)
    ledON(sgp30.eCO2, co2_l1, co2_l2, co2_l3, co2_l4, co2_l5)
    time.sleep(time_leds_on)
    led_blink(3,0.5)
    led(False)
    ledON(sgp30.TVOC, tvoc_l1, tvoc_l2, tvoc_l3, tvoc_l4, tvoc_l5)
    time.sleep(time_leds_on)
    led_blink(5,0.5)
    
    # Set baseline
    elapsed_sec += 1
    if elapsed_sec > 300:
        elapsed_sec = 0
        co2eq_base = sgp30.baseline_eCO2
        tvoc_base = sgp30.baseline_TVOC
        sgp30.set_iaq_baseline(co2eq_base, tvoc_base)
        if serial:
            print("**** Baseline: eCO2 = 0x%x, TVOC = 0x%x" % (co2eq_base, tvoc_base))
