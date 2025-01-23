import board
import pwmio
import time

btn = pwmio.PWMOut(board.GP16)

while True:
    btn.frequency = 0
    print("zero")
    time.sleep(4)
    btn.frequency = 100
    print("lights")
    time.sleep(4)
    btn.frequency = 4.5
    print("lock")
    time.sleep(4)
    
