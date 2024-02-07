import board
import pwmio
import time

btn = pwmio.PWMOut(board.GP16)

while True:
    btn.duty_cycle = 65535
    print("full")
    time.sleep(2)
    btn.duty_cycle = 60494
    print("open/close")
    time.sleep(2)
    btn.duty_cycle = 56060
    print("lights")
    time.sleep(2)
    btn.duty_cycle = 50000
    print("lock")
    time.sleep(2)
    btn.duty_cycle = 30000
    print("50%")
    time.sleep(2)
    btn.duty_cycle = 6500
    print("10")
    time.sleep(2)
