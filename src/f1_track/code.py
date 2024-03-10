import time
import board
import digitalio
import adafruit_hcsr04

trigDist = 10
sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP13, echo_pin=board.GP15)

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

t0 = time.monotonic_ns()
while True:
    dist = sonar.distance
     #print("distance:", sonar.distance)
    if dist < trigDist:
        t1 = time.monotonic_ns()
        print("Time:", str((t1-t0)*1e-9))
        t0 = time.monotonic_ns()
        led(True)
        time.sleep(0.1)
        led(False)
    time.sleep(0.1)
