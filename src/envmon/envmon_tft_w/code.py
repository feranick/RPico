
# **********************************************
# * Environmental Monitor TFT - Rasperry Pico W
# * v2024.01.08.3
# * By: Nicola Ferralis <feranick@hotmail.com>
# **********************************************

import os
import time
import ssl
import wifi
import socketpool
import microcontroller
import adafruit_requests

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

url = "https://api.weather.gov/"
user_agent = "(feranick, feranick@hotmail.com)"
headers = {'Accept': 'application/geo+json',
            'User-Agent' : user_agent}
            
############################
# User variable definitions
############################
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

def get_nws_data():
    try:
        response = requests.get(url, headers=Conf().headers).json())
        print("Text Response: ", response.text)
        response.close()
        data = [wdata['properties']['temperature']['value'],
            wdata['properties']['relativeHumidity']['value'],
            float(wdata['properties']['seaLevelPressure']['value'])/100))
                time.sleep(20)
        return response
    except:
        return [0,0,0]
    #except Exception as e:
    #    print("Error:\n", str(e))
    #    print("Resetting microcontroller in 10 seconds")
    #    time.sleep(10)
    #    microcontroller.reset()

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

############################
# Color and AQI color
############################
'''
color_bitmap = displayio.Bitmap(display.width, display.height, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x00FF00  # Bright Green
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)
'''
# Draw a smaller inner rectangle
rect1 = displayio.Bitmap(
    40, 85, 1
)
rect1_palette = displayio.Palette(1)
rect1_palette[0] = 0x000000  # Purple
rect1_sprite = displayio.TileGrid(
    rect1, pixel_shader=rect1_palette, x=280, y=0
)
splash.append(rect1_sprite)

# Draw a smaller inner rectangle
rect2 = displayio.Bitmap(
    40, 85, 1
)
rect2_palette = displayio.Palette(1)
rect2_palette[0] = 0x000000  # Purple
rect2_sprite = displayio.TileGrid(
    rect2, pixel_shader=rect2_palette, x=280, y=85
)
splash.append(rect2_sprite)

############################
# Labels 
############################
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
def AQI_CO2(c):
    if c <= 400:
        i = 1
        rect1_palette[0] = 0x00e408
    if c > 400 and c <= 1000:
        i = 2
        rect1_palette[0] = 0xffff00
    if c > 1000 and c <= 1500:
        i = 3
        rect1_palette[0] = 0xff8000
    if c > 1500 and c <= 2000:
        i = 4
        rect1_palette[0] = 0xff0000
    if c > 2000 and c <= 5000:
        i = 5
        rect1_palette[0] = 0x903f97
    if c > 5000:
        i = 6
        rect1_palette[0] = 0x7e0023
    return i
        
def AQI_TVOC(c):
    if c <= 50:
        i = 1
        rect2_palette[0] = 0x00e408
    if c > 50 and c <= 100:
        i = 2
        rect2_palette[0] = 0xffff00
    if c > 100 and c <= 150:
        i = 3
        rect2_palette[0] = 0xff8000
    if c > 150 and c <= 200:
        i = 4
        rect2_palette[0] = 0xff0000
    if c > 200 and c <= 300:
        i = 5
        rect2_palette[0] = 0x903f97
    if c > 300 and c <= 500:
        i = 6
        rect2_palette[0] = 0x7e0023
    return i

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

# change this to match the location's pressure (hPa) at sea level
# https://w1.weather.gov/data/obhistory/KBOS.html
# sea_level_pressure = 1029.3
bme280.sea_level_pressure = float(get_nws_data()[3])/100
elapsed_sec = 0

############################
# Main
############################
while True:
    # sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)
    
    nws = get_nws_data()
    
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
        print(" AQI-CO2: %d  AQI-TVOC: %d"  % (AQI_CO2(sgp30.eCO2), AQI_TVOC(sgp30.TVOC)))
        print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (sgp30.baseline_eCO2,
            sgp30.baseline_TVOC))

    labels[0].text = "Temp: %0.1f C (%0.1f C)" % (celsius, float(nws[0]))
    labels[1].text = "eCO2 = %d ppm" % sgp30.eCO2
    labels[2].text = "TVOC = %d ppb" % sgp30.TVOC
    labels[3].text = "AQI-CO2: %d  AQI-TVOC: %d"  % (AQI_CO2(sgp30.eCO2), AQI_TVOC(sgp30.TVOC))
    labels[5].text = "RH: %0.1f %% (%0.1f %%)" % (RH, float(nws[1]))
    labels[6].text = "Pressure: %0.1f hPa" % bme280.pressure
    labels[7].text = "Altitude = %0.2f meters" % bme280.altitude
    # labels[7].text = "eCO2: 0x%x TVOC:0x%x" % (sgp30.baseline_eCO2, sgp30.baseline_TVOC)
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
        bme280.sea_level_pressure = float(get_nws_data()[3])/100
