import time
import board
import digitalio
import random
import adafruit_hcsr04

trigDist = 30
sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP15, echo_pin=board.GP13)

while True:
    dist = sonar.distance
    print("distance:", sonar.distance)
    
    time.sleep(2)
