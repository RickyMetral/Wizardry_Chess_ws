from pynput import keyboard
import time


#Class to listen for any key on the keyboard being held. 
#Pass the on_held_callback and on_release_callback to run when the specified key is held and released
class KeyListener:
    def __init__(self, on_held_callback, on_release_callback, key: str):
        self.key_set = set()
        self.listener = keyboard.Listener(
            on_press = self.on_press,
            on_release = self.on_release
        )
        self.activation_key = key
        self.on_held_callback = on_held_callback
        self.on_release_callback = on_release_callback

    def on_press(self, key): 
        try:
            if key.char == self.activation_key and key not in self.key_set:
                self.key_set.add(key)
                self.on_held_callback()
        except AttributeError:
            pass

    def on_release(self, key):
        self.key_set.discard(key)
        self.on_release_callback()

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()


def test_held(key):
    print("q is being held", flush = True)

def test_release(key):
    print("q was released", flush = True)


def main():
    listener = KeyListener(test_held, test_release, key = 'q')
    listener.start()

    while True:
        time.sleep(0.1)
        pass


if __name__ == "__main__":
    main()




