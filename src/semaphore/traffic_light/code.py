import time
import board
import digitalio

t_red = 5
t_green = 5
t_yellow1 = 2
t_yellow2 = 1

led1 = digitalio.DigitalInOut(board.GP28)
led1.direction = digitalio.Direction.OUTPUT
led2 = digitalio.DigitalInOut(board.GP27)
led2.direction = digitalio.Direction.OUTPUT
led3 = digitalio.DigitalInOut(board.GP22)
led3.direction = digitalio.Direction.OUTPUT
led4 = digitalio.DigitalInOut(board.GP21)
led4.direction = digitalio.Direction.OUTPUT
led5 = digitalio.DigitalInOut(board.GP19)
led5.direction = digitalio.Direction.OUTPUT
ledY = digitalio.DigitalInOut(board.GP3)
ledY.direction = digitalio.Direction.OUTPUT
ledG = digitalio.DigitalInOut(board.GP8)
ledG.direction = digitalio.Direction.OUTPUT

def led(value):
    led1.value = value
    led2.value = value
    led3.value = value
    led4.value = value
    led5.value = value
    
def cycle():
    print("start green")
    ledG.value = True
    ledY.value = True
    led(True)
    time.sleep(t_red)
    print("stop green")
    ledY.value = False
    time.sleep(t_yellow1)
    ledY.value = True
    led(False)
    ledG.value = False
    time.sleep(t_green)
    ledY.value = False
    time.sleep(t_yellow2)
    ledY.value = True

while True:
    cycle()
