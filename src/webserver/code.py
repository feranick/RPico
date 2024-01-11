import wifi
import socketpool
import time

wifi.radio.connect("BudSpencer", "Pennstate123")
pool = socketpool.SocketPool(wifi.radio)
ip = str(wifi.radio.ipv4_address)
sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
sock.settimeout(None)
sock.bind((ip, 80))
sock.listen(2)
print("Listening")

def webpage(state):
  #Template HTML
  html = f"""
      <!DOCTYPE html>
      <html>
      <form action="./open?">
      <input type="submit" value="Open" />
      </form>
      <form action="./close?">
      <input type="submit" value="Close" />
      </form>
      <p>LED is {state}</p>
      </body>
      </html>
      """
  return str(html)

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
    if request == "/open?":
        state = "OPEN"
    elif request =="/close?":
        state = "CLOSE"
    html = webpage(state)
    conn.send(html)
    conn.close()
