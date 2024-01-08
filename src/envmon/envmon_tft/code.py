
# **********************************************
# * Environmental Monitor TFT - Rasperry Pico
# * v2024.01.08.1
# * By: Nicola Ferralis <feranick@hotmail.com>
# **********************************************
# import time
import board
import busio
import digitalio
import terminalio
import displayio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_sgp30

# Compatibility with CircuitPython 9.x.x or 8.x.x
try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

############################
# User variable definitions
############################
serial = False

co2eq_base = 0x958a
tvoc_base = 0x8ed3

# change this to match the location's pressure (hPa) at sea level
# https://w1.weather.gov/data/obhistory/KBOS.html
sea_level_pressure = 1025.8
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
# TFT initialization
############################
TEXT_SCALE = 2
ROWS = 9
ROTATION = 270

# Release any resources currently in use for the displays
displayio.release_displays()

spi_tft = busio.SPI(board.GP10, MISO=board.GP12, MOSI=board.GP11)
tft_cs = board.GP7
tft_dc = board.GP8
tft_rst = board.GP9

display_bus = FourWire(spi_tft, command=tft_dc,
    chip_select=tft_cs, reset=tft_rst)

display = ST7789(display_bus, width=320, height=170, colstart=35, rotation=ROTATION)

# Make the display context
splash = displayio.Group()
display.root_group = splash

labels = []
for s in range(ROWS):
    labels.append(label.Label(
        terminalio.FONT,
        text=" ",
        color=0xFFFFFF,
        scale=TEXT_SCALE,
        anchor_point=(0, 0),
        anchored_position=(0, 20*s),
        ))
    splash.append(labels[s])

############################
# Sensor initialization
############################
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
        print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (sgp30.baseline_eCO2,
            sgp30.baseline_TVOC))

    labels[0].text = "Temperature: %0.1f C" % celsius
    labels[2].text = "eCO2 = %d ppm" % sgp30.eCO2
    labels[3].text = "TVOC = %d ppb" % sgp30.TVOC
    labels[5].text = "Humidity: %0.1f %%" % RH
    labels[6].text = "Pressure: %0.1f hPa" % bme280.pressure
    labels[7].text = "Altitude = %0.2f meters" % bme280.altitude
    # time.sleep(0.5)

    # Set baseline
    elapsed_sec += 1
    if elapsed_sec > 300:
        elapsed_sec = 0
        co2eq_base = sgp30.baseline_eCO2
        tvoc_base = sgp30.baseline_TVOC
        sgp30.set_iaq_baseline(co2eq_base, tvoc_base)
        if serial:
            print("**** Baseline: eCO2 = 0x%x, TVOC = 0x%x" % (co2eq_base, tvoc_base))
