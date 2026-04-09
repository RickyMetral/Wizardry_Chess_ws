from gpiozero import Device, OutputDevice, InputDevice
from gpiozero.pins.lgpio import LGPIOFactory
import time
import os
import chess_common_py.chess_common_py.config as env

Device.pin_factory = LGPIOFactory(chip=4)

STEP = OutputDevice(env.X_STEP_PIN)
DIR  = OutputDevice(env.X_DIR_PIN)
EN   = OutputDevice(env.X_EN_PIN, active_high=False, initial_value=False)
EM  = OutputDevice(env.EM_PIN)
def enable():
    EN.on()

def disable():
    EN.off()


def test_magnet():
    print("Magnet on")
    EM.on()
    # EM.value = 1.0
    time.sleep(10)
    # EM.value = 0.2
    time.sleep(6)
    EM.off()
    print("Magnet off")

def step_motor(steps: int, direction: bool, delay: float = 0.001):
    enable()
    DIR.value = direction
    for _ in range(steps):
        STEP.on()
        time.sleep(delay)
        STEP.off()
        time.sleep(delay)
    disable()

def main():
    try:
        print("Starting motor test...")
        test_magnet()
        # step_motor(6400, direction=True, delay = 0.0005)
        time.sleep(1)
        # step_motor(6400, direction=False)

    finally:
        disable()
        STEP.close()
        DIR.close()
        EN.close()
        print("Done")

if __name__ == '__main__':
    main()