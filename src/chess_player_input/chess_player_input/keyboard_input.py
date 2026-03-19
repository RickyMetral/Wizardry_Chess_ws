from pynput import keyboard
import threading


#Class to listen for any key on the keyboard being held. 
#Pass the on_held_callback and on_release_callback to run when the specified key is held and released
class KeyListener:
    def __init__(self, on_held_callback, on_release_callback, key: str):
        self.key_set = set()
        keyboard.on_press_key(key, self.on_press)
        keyboard.on_release_key(key, self.on_release)
        self.on_held_callback = on_held_callback
        self.on_release_callback = on_release_callback

    def on_press(self, event): 
        if event.name not in self.key_set:
            self.key_set.add(event.name)
            self.on_held_callback()

    def on_release(self, event):
        self.key_set.discard(event.name)
        self.on_release_callback()

    def start(self):
        thread = threading.Thread(target=keyboard.wait, daemon=True)
        thread.start()

    def stop(self):
        keyboard.unhook_all()



