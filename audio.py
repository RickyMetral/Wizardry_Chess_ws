import subprocess
import time

# Record 5 seconds
print("Recording...")
proc = subprocess.Popen(
    ['parecord', '--channels=1', '--rate=44100',
     '--file-format=wav', 'recording.wav']
)
time.sleep(5)
proc.terminate()
proc.wait()
print("Done!")

# Play it back
print("Playing...")
subprocess.run(['paplay', 'recording.wav'])
print("Finished!")