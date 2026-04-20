import sounddevice as sd
import json
import queue
import sys
from vosk import Model, KaldiRecognizer

MODEL_PATH = "/home/ws/src/Wizardry_Chess_ws/vosk-model-small-en-us"

# --- CONFIGURATION ---
# Ensure this matches your model folder name

def test_microphone():
    # 1. Load the Model
    print(f"Loading model from {MODEL_PATH}...")
    try:
        model = Model(MODEL_PATH)
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Make sure the model folder is in the same directory as this script.")
        return

    # 2. Define the Grammar (Keep it simple for testing)
    # Using words instead of digits for better accuracy
    grammar = ["one", "two", "three", "four", "five", "six", "seven", "eight", 
               "a", "b", "c", "d", "e", "f", "g", "h", "move", "[unk]"]
    
    rec = KaldiRecognizer(model, 16000, json.dumps(grammar))

    # 3. Setup Audio Queue
    audio_queue = queue.Queue()

    def callback(indata, frames, time, status):
        """This function is called for every audio block by sounddevice."""
        if status:
            print(status, file=sys.stderr)
        audio_queue.put(bytes(indata))

    WORD_TO_DIGIT = {
        "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8"
    }

    def process_vosk_result(text):
        # Split the result into words (e.g., "e two e four")
        words = text.split()
        converted_words = [WORD_TO_DIGIT.get(w, w) for w in words]
    
        # Join them back together (e.g., "e2e4")
        return "".join(converted_words)

    # 4. Open Stream and Listen
    print("\n>>> MICROPHONE ACTIVE")
    print(">>> Say something like 'e two e four' or 'move a one'")
    print(">>> Press Ctrl+C to stop\n")

    try:
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            
            while True:
                data = audio_queue.get()
                if rec.AcceptWaveform(data):
                    # Final result (after a pause)
                    result = json.loads(rec.Result())
                    text = process_vosk_result(result['text'])
                    print(f"\nCONFIRMED: {text}")
                else:
                    # Partial result (as you speak)
                    partial = json.loads(rec.PartialResult())
                    if partial["partial"]:
                        print(f"Listening: {partial['partial']}", end='\r')

    except KeyboardInterrupt:
        print("\n\nTest stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    test_microphone()