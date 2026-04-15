from gpiozero import Device, OutputDevice, Button
from gpiozero.pins.lgpio import LGPIOFactory
import time

Device.pin_factory = LGPIOFactory(chip=4)

SQUARE_SIZE_MM = 50       
MICROSTEP = 8
REV_STEPS = 200 * MICROSTEP
BELT_PITCH_MM = 2
PULLEY_TEETH = 20
MM_PER_REV = PULLEY_TEETH * BELT_PITCH_MM
MM_PER_STEP = MM_PER_REV / REV_STEPS

X_STEP_PIN = 12
X_DIR_PIN = 16
X_EN_PIN = 22

Y_STEP_PIN = 6
Y_DIR_PIN = 26
Y_EN_PIN = 5

EM_PIN = 13


# Limit switch pins
X_MIN_PIN  = 17    # X axis minimum (home position)
X_MAX_PIN  = 18    # X axis maximum
Y_MIN_PIN  = 23    # Y axis minimum (home position)
Y_MAX_PIN  = 24    # Y axis maximum


class StepperMotor:
    def __init__(
        self,
        step_pin: int,
        dir_pin: int,
        en_pin: int,
        min_switch: Button = None,
        max_switch: Button = None
    ):
        self.step = OutputDevice(step_pin)
        self.dir  = OutputDevice(dir_pin)
        self.en   = OutputDevice(en_pin, active_high=False, initial_value=False)
        self.min_switch = min_switch
        self.max_switch = max_switch
        self.position   = 0   # Track position in steps


    def enable(self):
        self.en.on()

    def disable(self):
        self.en.off()

    def is_at_min(self) -> bool:
        if self.min_switch is None:
            return False
        return self.min_switch.is_pressed

    def is_at_max(self) -> bool:
        if self.max_switch is None:
            return False
        return self.max_switch.is_pressed

    def move_one_square_x(self, direction: bool, delay: float = 0.001):
        self.move_x_mm(self.square_size_mm, direction, delay)

    def move_one_square_y(self, direction: bool, delay: float = 0.001):
        self.move_y_mm(self.square_size_mm, direction, delay)

    def move(self, steps: int, direction: bool, delay: float = 0.001) -> int:
        """
        Returns number of steps actually taken.
        Stops early if limit switch triggered.
        """
        self.enable()
        self.dir.value = direction
        steps_taken = 0

        for _ in range(steps):
            # Check limits before each step
            if direction and self.is_at_max():
                print("Max limit switch triggered, stopping")
                break
            if not direction and self.is_at_min():
                print("Min limit switch triggered, stopping")
                break

            self.step.on()
            time.sleep(delay)
            self.step.off()
            time.sleep(delay)

            steps_taken += 1

        self.disable()
        return steps_taken

    def home(self, delay: float = 0.001):
        """Move towards min switch until triggered, then zero position"""
        if self.min_switch is None:
            print("No min switch configured, cannot home")
            return

        self.enable()
        self.dir.value = False  # Move towards min

        while not self.is_at_min():
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
        self.mm_per_step = MM_PER_STEP 
        self.square_size_mm = SQUARE_SIZE_MM 

        self._gx = 0
        self._gy = 0
        self._EM_ON = False
        
        self.x_min = Button(X_MIN_PIN, pull_up=True)
        self.x_max = Button(X_MAX_PIN, pull_up=True)
        self.y_min = Button(Y_MIN_PIN, pull_up=True)
        self.y_max = Button(Y_MAX_PIN, pull_up=True)

        # Pass switches to motors
        self.x_motor = StepperMotor(
            X_STEP_PIN, X_DIR_PIN, X_EN_PIN,
            min_switch=self.x_min,
            max_switch=self.x_max
        )
        self.y_motor = StepperMotor(
            Y_STEP_PIN, Y_DIR_PIN, Y_EN_PIN,
            min_switch=self.y_min,
            max_switch=self.y_max
        )

        self.em = OutputDevice(EM_PIN)

    def magnet_on(self):
        self.em.on()

    def magnet_off(self):
        self.em.off()

    def test_magnet(self):
        self.magnet_on()
        time.sleep(6)
        self.magnet_off()

    #True is negative x, False is positive x
    def move_x(self, steps: int, direction: bool, delay: float = 0.001) -> float:
        steps_taken = self.x_motor.move(steps, direction, delay)
        dir = (1 if direction == True else -1)
        self._gx += self.step_to_mm(steps_taken) * dir

        return steps_taken

    #Fase is negative y, True is positive y
    def move_y(self, steps: int, direction: bool, delay: float = 0.001) -> float :
        steps_taken = self.y_motor.move(steps, direction, delay)
        dir = (-1 if direction == True else 1)
        self._gy += self.step_to_mm(steps_taken) * dir

        return steps_taken

    def mm_to_step(self, distance_mm):
        return distance_mm/self.mm_per_step

    def step_to_mm(self, steps):
        return steps * self.mm_per_step

    def home_all(self, delay: float = 0.001):
        """Home both axes """
        print("Homing X...")
        self.x_motor.home(delay)
        self._gx = -2
        print("Homing Y...")
        self.y_motor.home(delay)
        self._gy = 1
        print("All axes homed")

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



