import time
import board
import digitalio
import random

t1 = 1
t_off = 5

led1 = digitalio.DigitalInOut(board.GP13)
led1.direction = digitalio.Direction.OUTPUT
led2 = digitalio.DigitalInOut(board.GP12)
led2.direction = digitalio.Direction.OUTPUT
led3 = digitalio.DigitalInOut(board.GP11)
led3.direction = digitalio.Direction.OUTPUT
led4 = digitalio.DigitalInOut(board.GP10)
led4.direction = digitalio.Direction.OUTPUT
led5 = digitalio.DigitalInOut(board.GP9)
led5.direction = digitalio.Direction.OUTPUT

def ledOFF():
    led1.value = False
    led2.value = False
    led3.value = False
    led4.value = False
    led5.value = False

while True:
    t2 = random.uniform(1, 4)
    led1.value = True
    time.sleep(t1)
    led2.value = True
    time.sleep(t1)
    led3.value = True
    time.sleep(t1)
    led4.value = True
    time.sleep(t1)
    led5.value = True
    time.sleep(t2)
    ledOFF()
    time.sleep(t_off)
