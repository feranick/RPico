# **********************************************
# * Garage Opener - Rasperry Pico W
# * v2025.10.01.1
# * By: Nicola Ferralis <feranick@hotmail.com>
# **********************************************

import wifi
import time
import microcontroller
import supervisor
import os
import busio
import board
import digitalio
import socketpool
from adafruit_datetime import datetime
import adafruit_ntp
import adafruit_hcsr04
import adafruit_mcp9808

# Import the necessary modules.
from adafruit_httpserver import Server, MIMETypes, Response

############################
# Initial WiFi/Safe Mode Check
############################
if supervisor.runtime.safe_mode_reason is not None:
    try:
        print("Performing initial WiFi radio state check/reset...")
        if wifi.radio.connected:
            print("Radio was connected, disconnecting first.")
            wifi.radio.stop_station()
            time.sleep(0.5)
            wifi.radio.start_station()

        print("Toggling WiFi radio enabled state...")
        wifi.radio.enabled = False
        time.sleep(1.0)
        wifi.radio.enabled = True
        time.sleep(1.0)
        print("Initial WiFi radio toggle complete.")
    except Exception as e:
        print(f"Error during initial WiFi radio toggle: {e}")

############################
# User variable definitions
############################
class Conf:
    def __init__(self):
        self.triggerDistance = 20.0
        try:
            trig_dist_env = os.getenv("triggerDistance")
            if trig_dist_env is not None:
                self.triggerDistance = float(trig_dist_env)
            else:
                print("Warning: 'triggerDistance' not found in settings.toml. Using default.")
        except ValueError:
            print(f"Warning: Invalid triggerDistance '{trig_dist_env}' in settings.toml. Using default.")

############################
# Server
############################
class GarageServer:
    def __init__(self, control, sensors):
        self.control = control
        self.sensors = sensors
        self.ntp = None
        self.server = None
        self.ip = "0.0.0.0"

        try:
            self.connect_wifi()
            self.setup_server()
            self.setup_ntp()
            print("\nDevice IP:", self.ip, "\nListening...")
        except RuntimeError as err:
            print(f"Initialization error: {err}")
            self.fail_reboot()
        except Exception as e:
            print(f"Unexpected critical error: {e}")
            self.fail_reboot()

    def fail_reboot(self):
        print("Rebooting in 5 seconds due to error...")
        time.sleep(5)
        self.reboot()

    def connect_wifi(self):
        ssid = os.getenv('CIRCUITPY_WIFI_SSID')
        password = os.getenv('CIRCUITPY_WIFI_PASSWORD')
        if ssid is None or password is None:
            raise RuntimeError("WiFi credentials not found.")

        MAX_WIFI_ATTEMPTS = 5
        attempt_count = 0
        time.sleep(5)
        while not wifi.radio.connected:
            if attempt_count >= MAX_WIFI_ATTEMPTS:
                raise RuntimeError("Failed to connect to WiFi after multiple attempts.")
            print(f"\nConnecting to WiFi (attempt {attempt_count + 1}/{MAX_WIFI_ATTEMPTS})...")
            try:
                wifi.radio.connect(ssid, password)
                time.sleep(2)
            except ConnectionError as e:
                print(f"WiFi Connection Error: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"WiFi other connect error: {e}")
                time.sleep(3)
            attempt_count += 1

        if wifi.radio.connected:
            self.ip = str(wifi.radio.ipv4_address)
            print("WiFi Connected!")
        else:
            raise RuntimeError("Failed to connect to WiFi.")

    def setup_server(self):
        pool = socketpool.SocketPool(wifi.radio)
        self.server = Server(pool, debug=True)

        # --- Routes ---

        # Root Route: Serves static/index.html
        @self.server.route("/")
        def base_route(request):
            return self._serve_static_file(request, 'static/index.html')

        # Run Control Route
        @self.server.route("/run")
        def run_control(request):
            print("Run Control via HTTP request")
            self.control.runControl()
            # Use simplified Response for 200 OK
            return Response(request, "OK")

        # Status Check Route (Placeholder)
        @self.server.route("/status")
        def update_status(request):
            # Use simplified Response for 200 OK
            return Response(request, "OK")

        # JSON API to get status and other data
        @self.server.route("/api/status")
        def api_status(request):
            state = self.sensors.checkStatusSonar()
            label = self.control.setLabel(state)
            temperature = self.sensors.getTemperature()
            date_time = self.getDateTime()

            json_content = '{' + \
                '"state":"' + state + '",' + \
                '"button_text":"' + label[0] + '",' + \
                '"button_color":"' + label[1] + '",' + \
                '"temperature":"' + temperature + '",' + \
                '"datetime":"' + date_time + '",' + \
                '"ip":"' + self.ip + '"' + \
                '}'

            headers = {"Content-Type": "application/json"}

            # Return the response using the compatible Response constructor
            return Response(request, json_content, headers=headers)

        @self.server.route("/favicon.ico")
        def favicon_route(request):
            return self._serve_static_file(request, 'static/favicon.ico', content_type="image/x-icon")

        # If using a PNG for an app icon:
        @self.server.route("/icon192.png")
        def icon_route(request):
            return self._serve_static_file(request, 'static/icon192.png', content_type="image/png")
            
        @self.server.route("/icon.png")
        def icon_route(request):
            return self._serve_static_file(request, 'static/icon.png', content_type="image/png")

        # Start the server
        self.server.start(host=self.ip, port=80)

    def _serve_static_file(self, request, filepath, content_type="text/html"):
        """Manually reads a file and returns an HTTP response with a customizable content type."""
        
        # Determine if the file should be read in binary mode
        is_binary = filepath.endswith(('.ico', '.png'))
        mode = "rb" if is_binary else "r"
        encoding = None if is_binary else 'utf-8'
        
        try:
            with open(filepath, mode, encoding=encoding) as f:
                content = f.read()
            
            headers = {"Content-Type": content_type}
            
            # The Response object handles both text (str) and binary (bytes) content
            return Response(request, content, headers=headers)
            
        except OSError as e:
            # Handle File Not Found or other OS errors
            print(f"Error opening or reading file {filepath}: {e}")
            try:
                # The response content here should be simple text
                return Response(request, "File Not Found", {}, 404)
            except Exception as e2:
                print(f"Could not set 404 status: {e2}")
                return Response(request, "File Not Found. Check console.")

    def serve_forever(self):
        while True:
            if not wifi.radio.connected:
                print("WiFi connection lost. Rebooting...")
                self.reboot()
                
            try:
                self.server.poll()
            except (BrokenPipeError, OSError) as e:
                if isinstance(e, OSError) and e.args[0] not in (32, 104):
                    print(f"Unexpected OSError in server poll: {e}")
                elif isinstance(e, BrokenPipeError):
                    pass
            except Exception as e:
                print(f"Unexpected critical error in server poll: {e}")
                
            time.sleep(0.01)

    def setup_ntp(self):
        try:
            self.ntp = adafruit_ntp.NTP(socketpool.SocketPool(wifi.radio), tz_offset=-5)
        except Exception as e:
            print(f"Failed to setup NTP: {e}")

    def reboot(self):
        time.sleep(2)
        microcontroller.reset()

    def getDateTime(self):
        if self.ntp and self.ntp.datetime:
            try:
                st = self.ntp.datetime
                return f"{st.tm_year:04}-{st.tm_mon:02}-{st.tm_mday:02} {st.tm_hour:02}:{st.tm_min:02}:{st.tm_sec:02}"
            except Exception as e:
                print(f"Error converting NTP time: {e}")
                return "Time N/A"
        return "Time N/A"

############################
# Control, Sensors, and Main
############################
class Control:
    def __init__(self):
        self.btn = digitalio.DigitalInOut(board.GP18)
        self.btn.direction = digitalio.Direction.OUTPUT
        self.btn.value = False

    def runControl(self):
        self.btn.value = True
        time.sleep(2)
        self.btn.value = False
        time.sleep(1)

    def setLabel(self, a):
        if a == "OPEN":
            return ["CLOSE", "red"]
        elif a == "CLOSE":
            return ["OPEN", "green"]
        else:
            return ["N/A", "orange"]

class Sensors:
    def __init__(self, conf):
        self.sonar = None
        self.mcp = None
        try:
            self.sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP15, echo_pin=board.GP14)
        except Exception as e:
            print(f"Failed to initialize HCSR04: {e}")

        self.trigDist = conf.triggerDistance
        i2c = busio.I2C(board.GP1, board.GP0)
        try:
            self.mcp = adafruit_mcp9808.MCP9808(i2c)
            self.avDeltaT = microcontroller.cpu.temperature - self.mcp.temperature
            print("mcp OK")
        except Exception as e:
            self.avDeltaT = 0
            print(f"Failed to initialize MCP9808: {e}")
        self.numTimes = 1


    def checkStatusSonar(self):
        if not self.sonar:
            print("Sonar not initialized.")
            return "N/A"
        nt = 0
        while nt < 2:
            try:
                dist = self.sonar.distance
                print("Distance: "+str(dist))
                if dist < self.trigDist:
                    st = "OPEN"
                else:
                    st = "CLOSE"
                time.sleep(0.5)
                return st
            except RuntimeError:
                print(" Check Sonar Status: Retrying!")
                nt += 1
                time.sleep(0.5)
        print(" Sonar status not available")
        return "N/A"

    def getTemperature(self):
        t_cpu = microcontroller.cpu.temperature
        if not self.mcp:
            print("MCP9808 not initialized. Using CPU temp with estimated offset.")
            if self.numTimes > 1 and self.avDeltaT != 0 :
                return f"{round(t_cpu - self.avDeltaT, 1)} C (CPU adj.)"
            else:
                return f"{round(t_cpu, 1)} C (CPU raw)"
        try:
            t_mcp = self.mcp.temperature
            delta_t = t_cpu - t_mcp
            if self.numTimes >= 2e+1:
                self.numTimes = int(1e+1)
            self.avDeltaT = (self.avDeltaT * self.numTimes + delta_t)/(self.numTimes+1)
            self.numTimes += 1
            print("Av. CPU/MCP T diff: "+str(self.avDeltaT)+" "+str(self.numTimes))
            time.sleep(1)
            return str(round(t_mcp,1)) + " C"
        except:
            print("MCP9806 not available. Av CPU/MCP T diff: "+str(self.avDeltaT))
            time.sleep(1)
            return str(round(t_cpu-self.avDeltaT, 1))+" C (CPU)"

def main():
    conf = Conf()
    control = Control()
    sensors = Sensors(conf)
    server = GarageServer(control, sensors)

    server.serve_forever()

main()
