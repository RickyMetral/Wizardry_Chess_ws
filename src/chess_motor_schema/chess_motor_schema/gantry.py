from gpiozero import Device, OutputDevice, Button, PWMOutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../chess_common_py/chess_common_py'))
from config import * 

Device.pin_factory = LGPIOFactory(chip=4)


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
        self.position   = 0

    def enable(self):
        self.en.on()

    def disable(self):
        self.en.off()

    def is_at_min(self) -> bool:
        if self.min_switch is None:
            return False
        return not self.min_switch.is_pressed

    def is_at_max(self) -> bool:
        if self.max_switch is None:
            return False
        return not self.max_switch.is_pressed

    def move(self, steps: int, direction: bool, delay: float = 0.001) -> int:
        """
        Returns number of steps actually taken.
        Stops early if limit switch triggered.
        """
        self.enable()
        self.dir.value = direction
        steps_taken = 0

        for _ in range(steps):
            if not direction and self.is_at_max() and CHECK_BOUNDARIES:
                print("Max limit switch triggered, stopping")
                break
            if direction and self.is_at_min() and CHECK_BOUNDARIES:
                print("Min limit switch triggered, stopping")
                break

            self.step.on()
            time.sleep(delay)
            self.step.off()
            time.sleep(delay)

            steps_taken += 1

        self.disable()
        return steps_taken

    def home(self, delay: float = 0.0001, timeout: float = 60.0):
        """Move towards min switch until triggered, then zero position"""
        if self.min_switch is None:
            print("No min switch configured, cannot home")
            return

        self.enable()
        self.dir.value = True #TODO Switch back to true
        start = time.time()

        while True:
            if time.time() - start > timeout:
                self.disable()
                return False
            if not self.dir.value and self.is_at_max():
                break
            if self.dir.value and self.is_at_min():
                break

            self.step.on()
            time.sleep(delay)
            self.step.off()
            time.sleep(delay)

        self.disable()
        return True


    def close(self):
        self.disable()
        self.step.close()
        self.dir.close()
        self.en.close()


class ServoMotor:
    """
    Controls a standard hobby servo via PWM.
    Most servos expect a 50Hz signal with pulse widths between 1ms (0 deg) and 2ms (180 deg).

    min_pulse_width and max_pulse_width are in seconds.
    """
    def __init__(
        self,
        pin: int,
        min_angle: float = 0.0,
        max_angle: float = 180.0,
        min_pulse_width=0.0005,  # 0.5ms
        max_pulse_width=0.0025,
        frame_width: float = 0.02         # 50Hz
    ):
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_pulse_width = min_pulse_width
        self.max_pulse_width = max_pulse_width
        self.frame_width = frame_width
        self._current_angle = None

        # PWMOutputDevice expects a value between 0 and 1
        # frequency = 1 / frame_width (50Hz default)
        self.pwm = PWMOutputDevice(pin, frequency=round(1 / frame_width))

    def _angle_to_duty(self, angle: float) -> float:
        """Converts an angle to a PWM duty cycle between 0 and 1"""
        angle = max(self.min_angle, min(self.max_angle, angle))
        pulse = self.min_pulse_width + (angle - self.min_angle) / \
                (self.max_angle - self.min_angle) * \
                (self.max_pulse_width - self.min_pulse_width)
        return pulse / self.frame_width

    def set_angle(self, angle: float):
        """Move servo to specified angle"""
        self.pwm.value = self._angle_to_duty(angle)
        self._current_angle = angle

    def get_angle(self) -> float:
        return self._current_angle

    def close(self):
        self.pwm.close()

class ChessGantry:
    def __init__(self):
        self.mm_per_step = MM_PER_STEP 
        self.square_size_mm = SQUARE_SIZE_MM 

        self._gx = 0
        self._gy = 0
        self._EM_ON = False
        
        self.x_min = Button(X_MIN_PIN, pull_up=True, hold_time = .1)
        self.x_max = Button(X_MAX_PIN, pull_up=True, hold_time = .1)
        self.y_min = Button(Y_MIN_PIN, pull_up=True, hold_time = .1)
        self.y_max = Button(Y_MAX_PIN, pull_up=True, hold_time = .1)

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
        self.z_servo = ServoMotor(SERVO_PIN)  # Add SERVO_PIN to config.py

    def magnet_on(self):
        self.em.on()

    def magnet_off(self):
        self.em.off()

    def test_magnet(self):
        self.magnet_on()
        time.sleep(20)
        self.magnet_off

    def raise_z(self):
        """Raise the Z axis to the up position"""
        self.z_servo.set_angle(SERVO_UP_ANGLE)    

    def lower_z(self):
        """Lower the Z axis to the down position"""
        self.z_servo.set_angle(SERVO_DOWN_ANGLE)  

    def set_z_angle(self, angle: float):
        """Set Z axis to an arbitrary angle"""
        self.z_servo.set_angle(angle)

    #True is negative x, False is positive x
    def move_x(self, steps: int, direction: bool, delay: float = GANTRY_SPEED) -> float:
        steps_taken = self.x_motor.move(steps, direction, delay)
        dir = (1 if direction == True else -1)
        self._gx += (self.step_to_mm(steps_taken) * dir)
        return steps_taken

    #False is negative y, True is positive y
    def move_y(self, steps: int, direction: bool, delay: float = GANTRY_SPEED) -> float:
        steps_taken = self.y_motor.move(steps, direction, delay)
        dir = (-1 if direction == True else 1)
        self._gy += (self.step_to_mm(steps_taken) * dir)
        return steps_taken

    def move_one_square_x(self, direction: bool, delay: float = GANTRY_SPEED):
        self.move_x(self.mm_to_step(self.square_size_mm), direction, delay)

    def move_one_square_y(self, direction: bool, delay: float = GANTRY_SPEED):
        self.move_y(self.mm_to_step(self.square_size_mm), direction, delay)

    def mm_to_step(self, distance_mm):
        return round(distance_mm / self.mm_per_step)

    def step_to_mm(self, steps):
        return steps * self.mm_per_step

    def home_all(self, delay: float = 0.001):
        """Home both axes"""
        print("Homing X...")
        self.x_motor.home(delay)
        self._gx = MIN_COL * SQUARE_SIZE_MM
        print("Homing Y...")
        self.y_motor.home(delay)
        self._gy =  MIN_ROW * SQUARE_SIZE_MM
        print("All axes homed")

    def close(self):
        self.x_motor.close()
        self.y_motor.close()
        self.em.close()
        self.z_servo.close()
        self.x_min.close()
        self.x_max.close()
        self.y_min.close()
        self.y_max.close()
        Device.pin_factory.close()


def main():
    gantry = ChessGantry()

    try:

        gantry.raise_z()
        time.sleep(1)
        # print("Testing X motor...")
        # step_size = gantry.mm_to_step(SQUARE_SIZE_MM)
        # gantry.move_x(step_size, direction=True,  delay=GANTRY_SPEED)
        # time.sleep(3)
        # print("Testing Y motor...")
        # gantry.move_y(step_size, direction=True, delay=GANTRY_SPEED)
        # time.sleep(3)
        # gantry.move_x(step_size, direction=False, delay=GANTRY_SPEED)
        # print("Testing X motor...")
        # time.sleep(3)
        # gantry.move_y(step_size, direction=False, delay=GANTRY_SPEED)
        # print("Testing Y motor...")
        # time.sleep(1)
        # gantry.lower_z()
        # time.sleep(1)

    finally:
        gantry.close()
        print("Done")


if __name__ == '__main__':
    main()