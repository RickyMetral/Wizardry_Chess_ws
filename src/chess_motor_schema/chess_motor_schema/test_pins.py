#!/usr/bin/env python3
"""Set all GPIO pins to HIGH using gpiozero."""

from gpiozero import OutputDevice

# All standard BCM GPIO pins on a Raspberry Pi
GPIO_PINS = [
    5, 6, 12, 13, 16, 17, 
    22, 23, 24, 25, 26, 27
]

def set_all_pins_high():
    pins = []

    while True:
        for pin in GPIO_PINS:
            try:
                device = OutputDevice(pin)
                device.off()
                pins.append(device)
                print(f"Pin {pin} set HIGH")
            except Exception as e:
                print(f"Pin {pin} skipped: {e}")

    print("Done. Press Enter to cleanup and exit...")
    input()

    for device in pins:
        device.close()

if __name__ == "__main__":
    set_all_pins_high()
