import winsound
import time

print("Testing beep sound in 3 seconds...")
time.sleep(3)

try:
    print("Playing Beep (1000 Hz for 0.5 sec)...")
    winsound.Beep(1000, 500)  # 1000 Hz for 500 ms
    print("Beep finished.")
except Exception as e:
    print(f"An error occurred with Beep: {e}")

print("\nTesting system 'Asterisk' sound in 2 seconds...")
time.sleep(2)

try:
    print("Playing system sound...")
    winsound.MessageBeep(winsound.MB_OK) # Play a standard "OK" sound
    print("System sound played.")
except Exception as e:
    print(f"An error occurred with MessageBeep: {e}")