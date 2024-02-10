import board
import digitalio
import time

btn = digitalio.DigitalInOut(board.GP18)
btn.direction = digitalio.Direction.OUTPUT

while True:
    btn.value = False
    print(btn.value)
    time.sleep(5)
    btn.value = True
    print(btn.value)
    time.sleep(5)
