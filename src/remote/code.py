import board
import digitalio
import wifi
import socketpool
import time

wifi.radio.connect("SSID", "Password")
pool = socketpool.SocketPool(wifi.radio)
ip = str(wifi.radio.ipv4_address)
sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
sock.settimeout(None)
sock.bind((ip, 80))
sock.listen(2)
print("Listening")

btn = digitalio.DigitalInOut(board.GP5)
btn.direction = digitalio.Direction.OUTPUT
btn.value = True

def webpage(state):
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
        height: 2500px;
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
      <p>Control is {state}</p>
      </body>
      </html>
      """
  return str(html)
  
def runControl(btn):
    btn.value = False
    time.sleep(1)
    btn.value = True
    time.sleep(1)

buf = bytearray(1024)
state = "CLOSE"
while True:
    conn, addr = sock.accept()
    conn.settimeout(None)

    size = conn.recv_into(buf, 1024)
    
    try:
        request = str(buf[:50]).split()[1]
    except:
        request = ""
    if request == "/run?":
        runControl(btn)
        state = "RUN"
    html = webpage(state)
    conn.send(html)
    conn.close()
