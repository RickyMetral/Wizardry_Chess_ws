from gpiozero import Device, OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
import time
import os

os.makedirs('logs', exist_ok=True)
os.chdir('logs')

Device.pin_factory = LGPIOFactory(chip=4)

SQUARE_SIZE = 0.05      # in meters
REV_DISTANCE = 0.05
MICROSTEP = 1
REV_STEPS = 200 / MICROSTEP

X_STEP_PIN = 12
X_DIR_PIN = 16
X_EN_PIN = 22

Y_STEP_PIN = 13
Y_DIR_PIN = 26
Y_EN_PIN = 6

EM_PIN = 5

class StepperMotor:
    def __init__(self, step_pin: int, dir_pin: int, en_pin: int):
        self.step = OutputDevice(step_pin)
        self.dir  = OutputDevice(dir_pin)
        self.en   = OutputDevice(en_pin, active_high=False, initial_value=False)

    def enable(self):
        self.en.on()

    def disable(self):
        self.en.off()

    def move(self, steps: int, direction: bool, delay: float = 0.001):
        self.enable()
        self.dir.value = direction
        for _ in range(steps):
            self.step.on()
            time.sleep(delay)
            self.step.off()
            time.sleep(delay)
        self.disable()

    def close(self):
        self.disable()
        self.step.close()
        self.dir.close()
        self.en.close()


class ChessGantry:
    def __init__(self):
        self.x_motor = StepperMotor(
            step_pin=X_STEP_PIN,
            dir_pin=X_DIR_PIN,
            en_pin=X_EN_PIN
        )
        self.y_motor = StepperMotor(
            step_pin=Y_STEP_PIN,   # Update with your actual Y pins
            dir_pin=Y_DIR_PIN,
            en_pin=Y_EN_PIN
        )
        self.em = OutputDevice(EM_PIN)

    def magnet_on(self):
        self.em.on()

    def magnet_off(self):
        self.em.off()

    def test_magnet(self):
        self.em.on()
        # EM.value = 1.0
        time.sleep(10)
        # EM.value = 0.2
        time.sleep(6)
        self.em.off()

    def move_x(self, steps: int, direction: bool, delay: float = 0.001):
        self.x_motor.move(steps, direction, delay)

    def move_y(self, steps: int, direction: bool, delay: float = 0.001):
        self.y_motor.move(steps, direction, delay)

    def move_xy(self, x_steps: int, x_dir: bool, y_steps: int, y_dir: bool, delay: float = 0.001):
        """Move both motors sequentially — x first then y"""
        self.move_x(x_steps, x_dir, delay)
        self.move_y(y_steps, y_dir, delay)

    def close(self):
        self.x_motor.close()
        self.y_motor.close()
        self.em.close()


def main():
    gantry = ChessGantry()

    try:
        print("Magnet on")
        gantry.test_magnet()
        print("Magnet off")

        print("Testing X motor...")
        gantry.move_x(3200, direction=True, delay=0.00009)
        time.sleep(1)
        gantry.move_x(3200, direction=False, delay=0.00009)
        time.sleep(1)

        print("Testing Y motor...")
        gantry.move_y(3200, direction=True, delay=0.00009)
        time.sleep(1)
        gantry.move_y(3200, direction=False, delay=0.00009)
        time.sleep(1)

        print("Testing XY move...")
        gantry.move_xy(3200, True, 3200, True, delay=0.00009)

    finally:
        gantry.close()
        print("Done")


if __name__ == '__main__':
    main()