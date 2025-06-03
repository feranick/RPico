
# **********************************************
# * Environmental Monitor TFT - Rasperry Pico W
# * v2025.06.03.2
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
from fourwire import FourWire

import supervisor
supervisor.set_next_code_file(filename='code.py', reload_on_error=True)

############################
# User variable definitions
############################
class Conf:
    def __init__(self):
        try:
            self.station = os.getenv("station")
            self.serial = bool(os.getenv("serial"))
        except KeyError: # If a key is not in os.environ (e.g. missing in settings.toml)
            print("A required setting was not found in settings.toml, using defaults.")
            self.station = "kbos"
            self.serial = True
        except Exception as e:
            print(f"Error reading settings: {e}")

        self.loadBaseline()

        self.url = "https://api.weather.gov/stations/"+self.station+"/observations/latest/"
        self.user_agent = "(feranick, feranick@hotmail.com)"
        self.headers = {'Accept': 'application/geo+json',
            'User-Agent' : self.user_agent}
        wifi_connected = False
        for attempt in range(3):
            try:
                wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
                time.sleep(0.5) # Allow DHCP to work
                pool = socketpool.SocketPool(wifi.radio)
                self.requests = adafruit_requests.Session(pool, ssl.create_default_context())
                self.ip = str(wifi.radio.ipv4_address)
                print(f"Connected to Wi-Fi. IP: {self.ip}")
                wifi_connected = True
                break # Exit loop on success
            except RuntimeError as err:
                print(f"Wi-Fi connection attempt {attempt + 1} failed: {err}")
                time.sleep(5) # Wait before retrying
            except OSError as err: # Can happen if SSID not found
                print(f"Wi-Fi OS error attempt {attempt + 1} failed: {err}")
                time.sleep(5)

        if not wifi_connected:
            print("Failed to connect to Wi-Fi after multiple attempts. Continuing in offline mode.")
            self.requests = None # Indicate that network requests should not be made
            self.ip = "N/A"
            # Optionally: microcontroller.reset() if online is critical

    def loadBaseline(self):
        try:
            with open("/sgp30_baselines.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    name, value = line.strip().split('=')
                if name == "CO2EQ_BASE":
                    self.co2eq_base = int(value, 16)
                elif name == "TVOC_BASE":
                    self.tvoc_base = int(value, 16)
            print("Loaded SGP30 baselines from /sgp30_baselines.txt")
        except (OSError, ValueError): # File not found, or content error
            print("No SGP30 baselines file found or error reading, trying config defaults/env.")

            self.co2eq_base = os.getenv("co2eq_base")
            self.tvoc_base = os.getenv("tvoc_base")
            if self.co2eq_base is not None and self.tvoc_base is not None:
                print("Loaded SGP30 baselines from settings.toml")
            else:
                print("No SGP30 baselines file found or error reading, using hardcoded defaults")
                self.co2eq_base = 0xfea3
                self.tvoc_base = 0xff19
                #self.co2eq_base = int(os.getenv("co2eq_base", "0xfea3"), 16)
                #self.tvoc_base = int(os.getenv("tvoc_base", "0xff19"), 16)

    ############################
    # Retrieve NVS data
    ############################
    def get_nws_data(self):
        default = [0,0,102000]
        data = []
        try:
            self.r = self.requests.get(self.url, headers=self.headers)
            #self.r.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            response_json = self.r.json()
            raw = [response_json['properties']['temperature']['value'],
                response_json['properties']['relativeHumidity']['value'],
                response_json['properties']['seaLevelPressure']['value']]
            for i in range(len(raw)):
                if raw[i] is None:
                    data.append(default[i])
                else:
                    data.append(float(raw[i]))
            self.r.close()
            return data
        except adafruit_requests.OutOfRetries:
            print("NWS: Too many retries (likely network issue)")
            return default
        except RuntimeError as e: # Covers socket errors, etc.
            print(f"NWS: Network error: {e}")
            return default
        except (KeyError, TypeError, ValueError) as e: # Problems with JSON structure or content
            print(f"NWS: Error parsing data: {e}")
            return default
        except Exception as e:
            print(f"NWS: An unexpected error occurred: {e}")
            return default
        finally:
            if hasattr(self, 'r') and self.r:
                self.r.close()

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
        for _ in range(15):
            time.sleep(1)
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
        h = 0x000000  # Default/error color (e.g., black)
        i = 0       # Default/error AQI category
        if c <= 400:
            i = 1
            h = 0x00e408  # Green
        elif c <= 1000: # c > 400 is implied
            i = 2
            h = 0xffff00  # Yellow
        elif c <= 1500:
            i = 3
            h = 0xff8000  # Orange
        elif c <= 2000:
            i = 4
            h = 0xff0000  # Red
        elif c <= 5000:
            i = 5
            h = 0x903f97  # Purple
        else:  # c > 5000
            i = 6
            h = 0x7e0023  # Maroon
        self.disp.rect1_palette[0] = h
        return i

    def AQI_TVOC(self,c):
        h = 0x000000  # Default/error color (e.g., black)
        i = 0       # Default/error AQI category
        if c <= 50:
            i = 1
            h = 0x00e408
        elif c > 50 and c <= 100:
            i = 2
            h = 0xffff00
        elif c > 100 and c <= 150:
            i = 3
            h = 0xff8000
        elif c > 150 and c <= 200:
            i = 4
            h = 0xff0000
        elif c > 200 and c <= 300:
            i = 5
            h = 0x903f97
        else: # c > 300
            i = 6
            h = 0x7e0023
        self.disp.rect2_palette[0] = h
        return i

    def saveBaseline(self, conf):
        new_co2_base = self.sgp30.baseline_eCO2
        new_tvoc_base = self.sgp30.baseline_TVOC
        if conf.co2eq_base != new_co2_base or conf.tvoc_base != new_tvoc_base:
            conf.co2eq_base = new_co2_base
            conf.tvoc_base = new_tvoc_base
            try:
                with open("/sgp30_baselines.txt", "w") as f:
                    f.write(f"CO2EQ_BASE={hex(conf.co2eq_base)}\n")
                    f.write(f"TVOC_BASE={hex(conf.tvoc_base)}\n")
                if conf.serial:
                    print("**** Successfully saved new baselines to /sgp30_baselines.txt")
            except OSError as e:
                if conf.serial:
                    print(f"**** Failed to save baselines: {e}")
     # The set_iaq_baseline call here is not strictly necessary if the sensor is continuously powered
     # as it's already using these baselines. It doesn't hurt, though.
     # sens.sgp30.set_iaq_baseline(conf.co2eq_base, conf.tvoc_base)

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
        aqi_co2_val = sens.AQI_CO2(sens.sgp30.eCO2) # Sets color and returns index
        aqi_tvoc_val = sens.AQI_TVOC(sens.sgp30.TVOC)
        if conf.serial:
            print("\n Temperature: %0.1fC (%0.1fC)" % (celsius, float(sens.nws[0])))
            print(" Humidity: %0.1f%% (%0.1f%%)" % (RH, float(sens.nws[1])))
            print(" Pressure: %0.1f hPa" % sens.bme280.pressure)
            print(" Altitude = %0.2f meters" % sens.bme280.altitude)
            print(" eCO2 = %d ppm" % sens.sgp30.eCO2)
            print(" TVOC = %d ppb" % sens.sgp30.TVOC)
            print(" AQI-CO2: %d  AQI-TVOC: %d"  % (aqi_co2_val, aqi_tvoc_val))
            print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (sens.sgp30.baseline_eCO2,
                sens.sgp30.baseline_TVOC))

        disp.labels[0].text = "Temp: %0.1fC (%0.1fC)" % (celsius, float(sens.nws[0]))
        disp.labels[1].text = "RH: %0.1f%% (%0.1f%%)" % (RH, float(sens.nws[1]))
        disp.labels[2].text = "eCO2 = %d ppm" % sens.sgp30.eCO2
        disp.labels[3].text = "TVOC = %d ppb" % sens.sgp30.TVOC
        disp.labels[4].text = "AQI-CO2: %d  AQI-TVOC: %d"  % (aqi_co2_val, aqi_tvoc_val)
        disp.labels[5].text = "Pressure: %0.1f hPa" % sens.bme280.pressure
        disp.labels[6].text = "Altitude = %0.2f meters" % sens.bme280.altitude
        disp.labels[7].text = "eCO2: 0x%x TVOC:0x%x" % (sens.sgp30.baseline_eCO2, sens.sgp30.baseline_TVOC)
        time.sleep(0.5)

        # Set baseline
        elapsed_sec += 1
        if elapsed_sec > 20:
            sens.nws = conf.get_nws_data()
            sens.saveBaseline(conf)
            elapsed_sec = 0
            conf.co2eq_base = sens.sgp30.baseline_eCO2
            conf.tvoc_base = sens.sgp30.baseline_TVOC
            sens.sgp30.set_iaq_baseline(conf.co2eq_base, conf.tvoc_base)
            if conf.serial:
                print("**** Baseline: eCO2 = 0x%x, TVOC = 0x%x" % (conf.co2eq_base, conf.tvoc_base))
            sens.bme280.sea_level_pressure = sens.nws[2]/100

        time.sleep(0.5)

main()
