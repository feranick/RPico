# **********************************************
# * Garage Opener - Rasperry Pico W
# * v2024.01.18.3
# * By: Nicola Ferralis <feranick@hotmail.com>
# **********************************************

import os
import board
import digitalio
import wifi
import socketpool
import time
import microcontroller
from adafruit_datetime import datetime, timezone
import adafruit_ntp
import adafruit_hcsr04

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
class Server:
    def __init__(self):
        try:
            wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'),
            os.getenv('CIRCUITPY_WIFI_PASSWORD'))
            time.sleep(0.5)
            pool = socketpool.SocketPool(wifi.radio)
            self.ip = str(wifi.radio.ipv4_address)
            self.sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
            self.sock.settimeout(None)
            self.sock.bind((self.ip, 80))
            self.sock.listen(2)
            self.ntp = adafruit_ntp.NTP(pool, tz_offset=0)
            print("\n Device IP: "+self.ip+"\n Listening...")
        except RuntimeError as err:
            print(err,"\n Restarting...")
            time.sleep(2)
            import microcontroller
            microcontroller.reset()
            print(err)

    def webpage(self, state, label):
        #Template HTML
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
        <form action="./run?">
        <input type="submit" id="Submit" value= {label} />
        </form>
        Door is {state}
        <form action="./status?">
        <input type="submit" id="Status" value="Update Status" />
        </form>
        <p>Temperature: {str(round(microcontroller.cpu.temperature,1))} C</p>
        <p>Device IP: {self.ip}</p>
        </body>
        </html>
        """
        return str(html)

    def getDateTime(self):
        st = self.ntp.datetime
        now = datetime(*st[:6])
        return now

############################
# User variable definitions
############################
class Control:
    def __init__(self):
        self.btn = digitalio.DigitalInOut(board.GP17)
        self.btn.direction = digitalio.Direction.OUTPUT
        self.btn.value = True

    def runControl(self):
        self.btn.value = False
        time.sleep(1)
        self.btn.value = True
        time.sleep(1)

    def setLabel(self, a):
        if a == "OPEN":
            return "CLOSE"
        elif a == "CLOSE":
            return "OPEN"
        else:
            return "N/A"

############################
# Sonar
############################
class Sonar:
    def __init__(self, conf):
        self.trigDist = conf.triggerDistance
        self.sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP15, echo_pin=board.GP14)

    def checkStatus(self):
        nt = 0
        while nt < 5:
            try:
                dist = self.sonar.distance
                print(dist)
                if dist < self.trigDist:
                    st = "OPEN"
                else:
                    st = "CLOSE"
                time.sleep(1)
                return st
            except RuntimeError:
                print(" Retrying!")
                nt+=1
                time.sleep(1)
        print(" Status not available")
        return "N/A"


############################
# Main
############################
def main():
    server = Server()
    control = Control()
    sonar = Sonar(Conf())

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
            control.runControl()

        state = sonar.checkStatus()
        html = server.webpage(state, control.setLabel(state))
        nt = 0
        while nt < 5:
            try:
                conn.send(html)
                time.sleep(1)
                break
            except ConnectionError:
                nt+=1

        conn.close()
        time.sleep(1)

main()
