"""Test a single button input using gpiozero."""

from gpiozero import Button

BUTTON_PIN = 12  # Change this to your button's BCM pin number

def main():
    button = Button(BUTTON_PIN, pull_up=True, hold_time = 0.02)

    print(f"Listening on pin {BUTTON_PIN}. Press Ctrl+C to exit.")

    # button.when_held = lambda: print("Button RELEASED")
    # button.when_released = lambda: print("Button HELD")

    try:
        while True:
            if button.is_held:
                print("Button Held")
            if button.is_pressed:
                print("Button released")
            pass
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        button.close()

if __name__ == "__main__":
    main()