import time
import board
import digitalio
import random
import adafruit_hcsr04

t1 = 1
t_off = 3

trigDist = 10
sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP11, echo_pin=board.GP13)

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
    
    
    '''dist = sonar.distance
    print("distance:", sonar.distance)
    if dist < trigDist:
        pass
        #t2 = random.uniform(1, 4)
        #led1.value = True
        #led2.value = True
        #led3.value = True
        #led4.value = True
        #led5.value = True
    else:
        ledOFF()
    time.sleep(0.5)
    '''
