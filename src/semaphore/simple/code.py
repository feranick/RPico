import time
import board
import digitalio
import random

t1 = 1
t_off = 3

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

while True:
    t2 = random.uniform(4, 8)
    ledY.value = True
    time.sleep(2)
    ledY.value = False
    ledG.value = False
    led(True)
    time.sleep(t2)
    ledY.value = True
    time.sleep(1)
    ledY.value = False
    led(False)
    ledG.value = True
    time.sleep(t2)
    
