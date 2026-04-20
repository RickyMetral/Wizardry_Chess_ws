import sys
import termios
import tty
import threading
import time

class KeyListener:
    #On press callback will receive the key pressed as a paramater
    def __init__(self, on_press_callback):
        self.on_press_callback = on_press_callback
        self.running = False
        self.thread = None
        # Save the original terminal settings to restore them later
        try:
            self.settings = termios.tcgetattr(sys.stdin)
        except termios.error:
            self.settings = None
            print("Warning: No TTY detected. Keyboard input may not work.")

    def _get_char(self):
        """Reads a single character from standard input."""
        tty.setraw(sys.stdin.fileno())
        # select allows us to read without blocking indefinitely
        import select
        if select.select([sys.stdin], [], [], 0.1)[0]:
            char = sys.stdin.read(1)
        else:
            char = None
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return char

    def _listen_loop(self):
        while self.running:
            char = self._get_char()
            if char:
                # Trigger the callback every time a key is detected
                self.on_press_callback(char)
            time.sleep(0.01)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        # Ensure terminal is back to normal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

def test_press(key):
    print(f"Key pressed: {key}", flush=True)

def main():
    # You no longer need to pass a specific key or release callback
    listener = KeyListener(test_press)
    print("Listening for key presses... (Press Ctrl+C to stop)")
    
    try:
        listener.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        listener.stop()

if __name__ == "__main__":
    main()