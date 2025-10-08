# **********************************************
# * Garage Opener - Rasperry Pico W
# * v2024.02.11.1
# * By: Nicola Ferralis <feranick@hotmail.com>
# **********************************************

import os
import busio
import board
import digitalio
import wifi
import socketpool
import time
import microcontroller
from adafruit_datetime import datetime
import adafruit_ntp
import adafruit_hcsr04
import adafruit_mcp9808
from adafruit_httpserver import Server, Request, Response, GET, POST

############################
# User variable definitions
############################
class Conf:
    def __init__(self):
        try:
            self.triggerDistance = float(os.getenv("trigDistance"))
        except:
            self.triggerDistance = 20
        
############################
# Server
############################
class ServeConf:
    def __init__(self, control, sensors):
        try:
            wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'),
            os.getenv('CIRCUITPY_WIFI_PASSWORD'))
            time.sleep(0.5)
            pool = socketpool.SocketPool(wifi.radio)
            self.ip = str(wifi.radio.ipv4_address)
            self.server = Server(pool, debug=True)
            #self.sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
            #self.sock.settimeout(None)
            #self.sock.bind((self.ip, 80))
            #self.sock.listen(2)
            self.ntp = adafruit_ntp.NTP(pool, tz_offset=-5)
            print("\n Device IP: "+self.ip+"\n Listening...")
        except RuntimeError as err:
            print(err, "\n Restarting...")
            time.sleep(2)
            import microcontroller
            microcontroller.reset()
            print(err)

    def webpage(self, state, label, temperature):
        # Template HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>Pico Garage Opener</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=0" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta names="apple-mobile-web-app-status-bar-style" content="black-translucent" />
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
        
        <a href="/form?run">
            <button>Run Control</strong> form</button>
        </a><br />
        <a href="/form?status">
            <button>Status</strong> form</button>
        </a><br />
        
        <form action="/form" method="post"">
            <input type="submit" value="Submit">
        </form>
        
        <br>Temperature: {temperature}
        <br><br><small><small>{self.getDateTime()}</small></small>
        <br><small><small>Device IP: {self.ip}</p></small></small>
        </body>
        </html>
        """
        return str(html)
        
    @self.server.route("/", [GET, POST])
    def form(self, request: Request):
        if request.method == GET:
            req = str(request.query_params)
            print("params:"+req)
            if req == "run=":
                print("Run Control")
                control.runControl()
                time.sleep(10)
            content_type="text/html",
            if req == "status=":
                print ("STATUS")
    
    def getDateTime(self):
        try:
            st = self.ntp.datetime
            now = datetime(*st[:6])
        except:
            now = ""
        return now
    

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
        self.trigDist = conf.triggerDistance
        self.sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP15, echo_pin=board.GP14)
        i2c = busio.I2C(board.GP1, board.GP0)
        self.mcp = adafruit_mcp9808.MCP9808(i2c)
        self.numTimes = 1
        self.avDeltaT = 0

    def checkStatusSonar(self):
        nt = 0
        while nt < 5:
            try:
                dist = self.sonar.distance
                print("Distance: "+str(dist))
                if dist < self.trigDist:
                    st = "OPEN"
                else:
                    st = "CLOSE"
                time.sleep(1)
                return st
            except RuntimeError:
                print(" Check Sonar Status: Retrying!")
                nt += 1
                time.sleep(1)
        print(" Sonar status not available")
        return "N/A"

    def getTemperature(self):
        t_cpu = microcontroller.cpu.temperature
        try:
            t_mcp = self.mcp.temperature
            delta_t = t_cpu - t_mcp
            if self.numTimes >= 2e+1:
                self.numTimes = int(1e+1)
            self.avDeltaT = (self.avDeltaT * self.numTimes + delta_t)/(self.numTimes+1)
            self.numTimes += 1
            print("Av. CPU/MCP T diff: "+str(self.avDeltaT)+" "+str(self.numTimes))
            time.sleep(1)
            return str(round(t_mcp,1))+" C"
        except:
            print("MCP9806 not available. Av CPU/MCP T diff: "+str(self.avDeltaT))
            time.sleep(1)
            return str(round(t_cpu-self.avDeltaT, 1))+" C (CPU)"

############################
# Main
############################
def main():
    control = Control()
    sensors = Sensors(Conf())
    serv = ServeConf(control, sensors)
    
    serv.server.serve_forever(serv.ip)
    
    '''
    buf = bytearray(1024)
    state = "N/A"

    while True:
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
            time.sleep(10)

        state = sensors.checkStatusSonar()
        html = server.webpage(state, control.setLabel(state), sensors.getTemperature())
        nt = 0
        while nt < 2:
            try:
                conn.send(html)
                time.sleep(1)
                break
            except ConnectionError:
                nt += 1

        conn.close()
        time.sleep(1)
        '''

main()
