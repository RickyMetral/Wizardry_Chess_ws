import speech_recognition as sr
from keyboard_input import KeyListener


class SpeechRecognizer:
    def __init__(self, key):
        self.key_listener = KeyListener(self.listen, self.stop_listening, key)
        self.r = sr.Recognizer()   
        self.audio = None

    def listen(self):
        try:
            with sr.Microphone() as source:
                print("Listening...")
            
                self.r.adjust_for_ambient_noise(source, duration=0.2)
                self.audio = self.r.listen(source)
            
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))

        except sr.UnknownValueError:
            print("Could not understand audio")

        except KeyboardInterrupt:
            print("Program terminated by user")


    def stop_listening(self):
        if not self.audio:
            print("No audio recorded")
            return
        try:
            text = self.r.recognize_google(self.audio)
            text = text.lower()  
            print("You said:", text)

        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results: {e}")

    def start(self):
        self.key_listener.start()
    
    def stop(self):
        self.key_listener.stop()

if __name__ == "__main__":
    speech = SpeechRecognizer("q")
    speech.start()
    try: 
        while True:
            pass
    except KeyboardInterrupt:
        speech.stop()
