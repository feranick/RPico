
# **********************************************
# * Environmental Monitor TFT - Rasperry Pico W
# * v2025.01.30.1
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
    
import supervisor
supervisor.set_next_code_file(filename='code.py', reload_on_error=True)

############################
# User variable definitions
############################
class Conf:
    def __init__(self):
        try:
            self.station = os.getenv("station")
            self.co2eq_base = os.getenv("co2eq_base")
            self.tvoc_base = os.getenv("tvoc_base")
            self.serial = bool(os.getenv("serial"))
        except:
            self.station = "kbos"
            self.co2eq_base = 0x8ce0
            self.tvoc_base = 0x91e4
            self.serial = True

        self.url = "https://api.weather.gov/stations/"+self.station+"/observations/latest/"
        self.user_agent = "(feranick, feranick@hotmail.com)"
        self.headers = {'Accept': 'application/geo+json',
            'User-Agent' : self.user_agent}
        try:
            wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'),
            os.getenv('CIRCUITPY_WIFI_PASSWORD'))
            time.sleep(0.5)
            pool = socketpool.SocketPool(wifi.radio)
            self.requests = adafruit_requests.Session(pool, ssl.create_default_context())
            self.ip = str(wifi.radio.ipv4_address)
            time.sleep(2)
        except RuntimeError as err:
            print(err,"\n Restarting...")
            time.sleep(2)
            import microcontroller
            microcontroller.reset()
            print(err)

    ############################
    # Retrieve NVS data
    ############################
    def get_nws_data(self):
        default = [0,0,102000]
        data = []
        try:
            self.r = self.requests.get(self.url, headers=self.headers)
            raw = [self.r.json()['properties']['temperature']['value'],
                self.r.json()['properties']['relativeHumidity']['value'],
                self.r.json()['properties']['seaLevelPressure']['value']]
            for i in range(len(raw)):
                if raw[i] is None:
                    data.append(default[i])
                else:
                    data.append(float(raw[i]))
            self.r.close()
            return data
        except:
            return default
        #except Exception as e:
        #    print("Error:\n", str(e))
        #    print("Resetting microcontroller in 10 seconds")
        #    time.sleep(10)
        #    microcontroller.reset()

############################
# TFT initialization
############################
class Display:
    def __init__(self):
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
        self.splash = displayio.Group()
        display.root_group = self.splash

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
        self.rect1 = displayio.Bitmap(40, 85, 1)
        self.rect1_palette = displayio.Palette(1)
        self.rect1_palette[0] = 0x000000  # Purple
        rect1_sprite = displayio.TileGrid(
        self.rect1, pixel_shader=self.rect1_palette, x=280, y=0
        )
        self.splash.append(rect1_sprite)

        # Draw a smaller inner rectangle
        self.rect2 = displayio.Bitmap(40, 85, 1)
        self.rect2_palette = displayio.Palette(1)
        self.rect2_palette[0] = 0x000000  # Purple
        rect2_sprite = displayio.TileGrid(
        self.rect2, pixel_shader=self.rect2_palette, x=280, y=85
        )
        self.splash.append(rect2_sprite)

        ############################
        # Labels
        ############################
        self.labels = []
        for s in range(ROWS):
            self.labels.append(label.Label(
                terminalio.FONT,
                text=" ",
                color=0xFFFFFF,
                scale=TEXT_SCALE,
                anchor_point=(0, 0),
                anchored_position=(0, 20*s),
                ))
            self.splash.append(self.labels[s])

############################
# Sensor initialization
############################
class Sensors:
    def __init__(self, conf, disp):
        self.conf = conf
        self.disp = disp
        spi = busio.SPI(board.GP18, MISO=board.GP16, MOSI=board.GP19)
        bme_cs = digitalio.DigitalInOut(board.GP17)
        self.bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)

        i2c = busio.I2C(board.GP1, board.GP0, frequency=100000)
        self.sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
        self.sgp30.iaq_init()
        el_sec = 0
        if conf.serial:
            print("SGP30 sensor Warming up...")
        while el_sec < 30:
            time.sleep(0.5)
            el_sec += 1
        self.sgp30.set_iaq_baseline(conf.co2eq_base, conf.tvoc_base)
        if conf.serial:
            print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (conf.co2eq_base, conf.tvoc_base))

        # change this to match the location's pressure (hPa) at sea level
        # https://w1.weather.gov/data/obhistory/KBOS.html
        # sea_level_pressure = 1029.3

        disp.labels[2].text = "Retrieving NWS data"
        disp.labels[3].text = "For station: "+conf.station
        disp.labels[5].text = "IP: "+self.conf.ip

        self.nws = conf.get_nws_data()
        self.bme280.sea_level_pressure = self.nws[2]/100
        disp.labels[2].text = "                      "
        disp.labels[3].text = "                      "
        disp.labels[5].text = "                      "

    ############################
    # Sensor initialization
    ############################
    def AQI_CO2(self,c):
        if c <= 400:
            i = 1
            h = 0x00e408
        if c > 400 and c <= 1000:
            i = 2
            h = 0xffff00
        if c > 1000 and c <= 1500:
            i = 3
            h = 0xff8000
        if c > 1500 and c <= 2000:
            i = 4
            h = 0xff0000
        if c > 2000 and c <= 5000:
            i = 5
            h = 0x903f97
        if c > 5000:
            i = 6
            h = 0x7e0023
        self.disp.rect1_palette[0] = h
        return i

    def AQI_TVOC(self,c):
        if c <= 50:
            i = 1
            h = 0x00e408
        if c > 50 and c <= 100:
            i = 2
            h = 0xffff00
        if c > 100 and c <= 150:
            i = 3
            h = 0xff8000
        if c > 150 and c <= 200:
            i = 4
            h = 0xff0000
        if c > 200 and c <= 300:
            i = 5
            h = 0x903f97
        if c > 300:
            i = 6
            h = 0x7e0023
        self.disp.rect2_palette[0] = h
        return i

############################
# Main
############################
def main():
    conf = Conf()
    disp = Display()
    sens = Sensors(conf, disp)

    elapsed_sec = 0
    while True:

        celsius = sens.bme280.temperature
        RH = sens.bme280.relative_humidity
        sens.sgp30.set_iaq_relative_humidity(celsius=celsius, relative_humidity=RH)
        if conf.serial:
            print("\n Temperature: %0.1fC (%0.1fC)" % (celsius, float(sens.nws[0])))
            print(" Humidity: %0.1f%% (%0.1f%%)" % (RH, float(sens.nws[1])))
            print(" Pressure: %0.1f hPa" % sens.bme280.pressure)
            print(" Altitude = %0.2f meters" % sens.bme280.altitude)
            print(" eCO2 = %d ppm" % sens.sgp30.eCO2)
            print(" TVOC = %d ppb" % sens.sgp30.TVOC)
            print(" AQI-CO2: %d  AQI-TVOC: %d"  % (sens.AQI_CO2(sens.sgp30.eCO2), sens.AQI_TVOC(sens.sgp30.TVOC)))
            print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (sens.sgp30.baseline_eCO2,
                sens.sgp30.baseline_TVOC))

        disp.labels[0].text = "Temp: %0.1fC (%0.1fC)" % (celsius, float(sens.nws[0]))
        disp.labels[1].text = "RH: %0.1f%% (%0.1f%%)" % (RH, float(sens.nws[1]))
        disp.labels[2].text = "eCO2 = %d ppm" % sens.sgp30.eCO2
        disp.labels[3].text = "TVOC = %d ppb" % sens.sgp30.TVOC
        disp.labels[4].text = "AQI-CO2: %d  AQI-TVOC: %d"  % (sens.AQI_CO2(sens.sgp30.eCO2), sens.AQI_TVOC(sens.sgp30.TVOC))
        disp.labels[5].text = "Pressure: %0.1f hPa" % sens.bme280.pressure
        disp.labels[6].text = "Altitude = %0.2f meters" % sens.bme280.altitude
        disp.labels[7].text = "eCO2: 0x%x TVOC:0x%x" % (sens.sgp30.baseline_eCO2, sens.sgp30.baseline_TVOC)
        time.sleep(0.5)

        # Set baseline
        elapsed_sec += 1
        if elapsed_sec > 3600:
            sens.nws = conf.get_nws_data()
            elapsed_sec = 0
            conf.co2eq_base = sens.sgp30.baseline_eCO2
            conf.tvoc_base = sens.sgp30.baseline_TVOC
            sens.sgp30.set_iaq_baseline(conf.co2eq_base, conf.tvoc_base)
            if conf.serial:
                print("**** Baseline: eCO2 = 0x%x, TVOC = 0x%x" % (conf.co2eq_base, conf.tvoc_base))
            sens.bme280.sea_level_pressure = sens.nws[2]/100

        time.sleep(0.5)
        
main()
