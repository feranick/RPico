# **********************************************
# * Garage Opener - Rasperry Pico W
# * v2025.09.30.1
# * By: Nicola Ferralis <feranick@hotmail.com>
# **********************************************

import wifi
import time
import microcontroller
import supervisor

if supervisor.runtime.safe_mode_reason is not None:
    try:
        print("Performing initial WiFi radio state check/reset...")
        if wifi.radio.connected:
            print("Radio was connected, disconnecting first.")
            wifi.radio.stop_station() # Requires CircuitPython 8+
            time.sleep(0.5)
            wifi.radio.start_station()

        print("Toggling WiFi radio enabled state...")
        wifi.radio.enabled = False
        time.sleep(1.0) # Increased delay
        wifi.radio.enabled = True
        time.sleep(1.0) # Increased delay
        print("Initial WiFi radio toggle complete.")
    except Exception as e:
        print(f"Error during initial WiFi radio toggle: {e}")
        # Decide if you want to proceed or perhaps trigger a safe mode or longer delay

import os
import busio
import board
import digitalio
import socketpool
import time
from adafruit_datetime import datetime
import adafruit_ntp
import adafruit_hcsr04
import adafruit_mcp9808

supervisor.set_next_code_file(filename='code.py', reload_on_error=True)

############################
# User variable definitions
############################
class Conf:
    def __init__(self):
        self.triggerDistance = 20.0 # Default to float
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
class Server:
    def __init__(self):
        try:
            self.connect_wifi()
            self.setup_server()
            self.setup_ntp()
            print("\nDevice IP:", self.ip, "\nListening...")
        except RuntimeError as err:
            print(f"Initialization error: {err}")
            print("Rebooting in 5 seconds...")
            time.sleep(5)
            self.reboot()
        except Exception as e: # Catch any other unexpected error during init
            print(f"Unexpected critical error: {e}")
            print("Rebooting in 5 seconds due to unexpected error...")
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
        while not bool(wifi.radio.connected): # Use wifi.radio.connected directly
            if attempt_count >= MAX_WIFI_ATTEMPTS:
                raise RuntimeError("Failed to connect to WiFi after multiple attempts.")
            print(f"\nConnecting to WiFi (attempt {attempt_count + 1}/{MAX_WIFI_ATTEMPTS})...")
            try:
                wifi.radio.connect(ssid, password)
                time.sleep(2) # Give a bit more time
            except ConnectionError as e:
                print(f"WiFi Connection Error: {e}")
                time.sleep(5) # Wait longer on connection errors
            except Exception as e: # Other potential errors like OSError
                print(f"WiFi other connect error: {e}")
                time.sleep(3)
            attempt_count += 1
        if wifi.radio.connected:
            print("WiFi Connected!")
        else:
            raise RuntimeError("Failed to connect to WiFi.") # Should be caught by previous check

    def check_connection(self):
        if not bool(wifi.Radio.connected):
            self.reboot()

    def setup_server(self):
        self.pool = socketpool.SocketPool(wifi.radio)
        self.ip = str(wifi.radio.ipv4_address)
        self.sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_STREAM)
        self.sock.settimeout(None)
        self.sock.bind((self.ip, 80))
        #self.sock.bind(('', 80))
        self.sock.listen(2)

    def setup_ntp(self):
        try:
            self.ntp = adafruit_ntp.NTP(self.pool, tz_offset=-5)
        except Exception as e: # Catch specific errors like OSError if possible
            print(f"Failed to setup NTP: {e}")

    def reboot(self):
        time.sleep(2)
        import microcontroller
        microcontroller.reset()

    def webpage(self, state, label, temperature):
        # Template HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>Pico Garage Opener</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=0" />
        <meta name="mobile-web-app-capable" content="yes" />
        <link rel="manifest" href='data:application/manifest+json,{{ "name": "Pico Garage Opener", 
            "short_name": "Pico Garage Opener", 
            "description": "Pico Garage Opener", 
            "start_url": ".", 
            "display": "standalone",
            }}' />
        </head>
        <body>
        <style type="text/css">
        #Submit {{
        background-color: {label[1]};
        color: white;
        font-size: 20px;
        font-weight: bold;
        margin: 70px;
        margin-top: 10px;
        height: 200px;
        width: 250px;
        position: center;
        text-align: center;
        border-width: 4px 4px;
        position:center;
        right:0px;
        padding: 0px;}}
        #Status {{
        font-size: 20px;
        font-weight: bold;
        margin: 70px;
        margin-top: 10px;
        height: 100px;
        width: 250px;
        position: center;
        text-align: center;
        border-width: 4px 4px;
        position:center;
        right:0px;
        padding: 0px;}}
        body{{
        margin: 5px;
        font-family: Helvetica;
        text-align: center;
        min-height: 30px;
        width: 100%;
        background-position: center top;
        text-align: center;
        font-size: 20px;
        padding: 11px 0px 12px 0px;
        font-weight: bold;}}
        .hidden{{display: none;}}
        .show{{display: block;}}
        .done{{opacity:0.2;}}
        .notdone{{opacity:1;}}
        </style>
        <script language="javascript" >
        function waitWarn(a) {{
        document.getElementById("warnLabel").innerHTML = "Please wait...";
        document.getElementById("Submit").disabled = true;
        document.getElementById("Status").disabled = true;
        if (a == 0) {{
            document.submitForm.submit();}}
        if (a == 1) {{
            document.statusForm.submit();}}
        }}
        </script>
        <form name="submitForm" action="./run?">
        <input type="submit" id="Submit" value= {label[0]} onclick=waitWarn(0) />
        </form>
        Door is {state}
        <form name="statusForm" action="./status?">
        <input type="submit" id="Status" value="Update Status" onclick=waitWarn(1) />
        <br><label id="warnLabel">Ready</label>
        </form>
        <br>Temperature: {temperature}
        <br><br><small><small>{self.getDateTime()}</small></small>
        <br><small><small>Device IP: {self.ip}</small></small>
        <br><small><small>Version 2025.09.30.1</small></small>
        </body>
        </html>
        """
        return str(html)

    def getDateTime(self):
        if self.ntp and self.ntp.datetime: # Check ntp object and if datetime is available
            try:
                st = self.ntp.datetime
                # Format the datetime object as a string if needed, e.g.:
                return f"{st.tm_year:04}-{st.tm_mon:02}-{st.tm_mday:02} {st.tm_hour:02}:{st.tm_min:02}:{st.tm_sec:02}"
            except Exception as e:
                print(f"Error converting NTP time: {e}")
                return "Time N/A"
        return "Time N/A"


############################
# User variable definitions
############################
class Control:
    def __init__(self):
        self.btn = digitalio.DigitalInOut(board.GP18)
        self.btn.direction = digitalio.Direction.OUTPUT
        self.btn.value = False  # Set this: True for remote control; False for direct.

    # Version with Transistor and remote control
    def runControl(self):
        self.btn.value = True
        time.sleep(2)
        self.btn.value = False
        time.sleep(1)

    # Version with Transistor and direct
    '''
    def runControl(self):
        self.btn.value = False
        time.sleep(2)
        self.btn.value = True
        time.sleep(1)
    '''

    def setLabel(self, a):
        if a == "OPEN":
            return ["CLOSE", "red"]
        elif a == "CLOSE":
            return ["OPEN", "green"]
        else:
            return ["N/A", "orange"]

############################
# Sensors
############################
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
            # Use self.avDeltaT only if it has been meaningfully calculated
            if self.numTimes > 1 and self.avDeltaT != 0 : # Check if avDeltaT has been updated
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

############################
# Main
############################
def main():
    server = Server()
    control = Control()
    sensors = Sensors(Conf())

    buf = bytearray(1024)
    state = "N/A"

    while True:
        server.check_connection()
        conn, addr = server.sock.accept()
        conn.settimeout(None)

        size = conn.recv_into(buf, 1024)

        try:
            request = str(buf[:50]).split()[1]
        except:
            request = ""
        if request == "/run?":
            print("Run Control")
            control.runControl()
            #time.sleep(10)

        state = sensors.checkStatusSonar()
        html = server.webpage(state, control.setLabel(state), sensors.getTemperature())
        nt = 0
        while nt < 10:
            try:
                conn.send(html)
                time.sleep(1)
                conn.close()
                break
            except ConnectionError as err:
                nt += 1
                time.sleep(1)
                if nt == 5:
                    server.reboot()
main()
