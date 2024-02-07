import board
import digitalio
import time

btn = digitalio.DigitalInOut(board.GP16)
btn.direction = digitalio.Direction.OUTPUT

while True:
    btn.value = False
    print(btn.value)
    time.sleep(3)
    btn.value = True
    print(btn.value)
    time.sleep(3)
