# **********************************************
# * Garage Opener - Rasperry Pico W
# * v2024.01.12.1
# * By: Nicola Ferralis <feranick@hotmail.com>
# **********************************************

import os
import board
import digitalio
import wifi
import socketpool
import time

############################
# User variable definitions
############################
class Conf:
    def __init__(self):
        try:
            wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'),
            os.getenv('CIRCUITPY_WIFI_PASSWORD'))
            pool = socketpool.SocketPool(wifi.radio)
            self.ip = str(wifi.radio.ipv4_address)
            self.sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
            self.sock.settimeout(None)
            self.sock.bind((self.ip, 80))
            self.sock.listen(2)
            print("\n Device IP: "+self.ip+"\n Listening")
        except:
            pass

        self.btn = digitalio.DigitalInOut(board.GP26)
        self.btn.direction = digitalio.Direction.OUTPUT
        self.btn.value = True

    def webpage(self, state):
        #Template HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=0" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta names="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        </head>
        <body>
        <style type="text/css">
        #Submit {{
        font-size: 20px;
        font-weight: bold;
        margin: 200px;
        margin-top: 10px;
        height: 250px;
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
        text-align: left;
        font-size: 20px;
        padding: 11px 0px 12px 0px;
        font-weight: bold;}}
        .hidden{{display: none;}}
        .show{{display: block;}}
        .done{{opacity:0.2;}}
        .notdone{{opacity:1;}}
        </style>
        <form action="./run?">
        <input type="submit" id="Submit" value="Run" />
        </form>
        <p>Device IP: {self.ip}</p>
        <p>Control is {state}</p>
        </body>
        </html>
        """
        return str(html)
  
    def runControl(self):
        self.btn.value = False
        time.sleep(1)
        self.btn.value = True
        time.sleep(1)

############################
# Main
############################
def main():
    conf = Conf()

    buf = bytearray(1024)
    state = "CLOSE"
    
    while True:
        conn, addr = conf.sock.accept()
        conn.settimeout(None)

        size = conn.recv_into(buf, 1024)
    
        try:
            request = str(buf[:50]).split()[1]
        except:
            request = ""
        if request == "/run?":
            conf.runControl()
            state = "RUN"
        html = conf.webpage(state)
        conn.send(html)
        conn.close()

main()
