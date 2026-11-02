import cv2
import numpy as np
import pyttsx3
import time

# Initialize Voice
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

cap = cv2.VideoCapture(0)
last_alarm_time = 0

print("[INFO] Starting Visual Fire Detector. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Blur the frame to reduce noise
    blur = cv2.GaussianBlur(frame, (15, 15), 0)
    
    # Convert BGR to HSV for accurate color detection
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    # Define the HSV color range for Fire (Yellow/Orange/Red)
    lower_fire = np.array([18, 50, 50], dtype=np.uint8)
    upper_fire = np.array([35, 255, 255], dtype=np.uint8)

    # Create a mask to extract only the fire colors
    mask = cv2.inRange(hsv, lower_fire, upper_fire)
    
    # Find contours (shapes) of the fire
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    fire_detected = False

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000: # Minimum size of the fire to ignore small sparks/lights
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 3)
            cv2.putText(frame, "FIRE ACCIDENT DETECTED!", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            fire_detected = True

    if fire_detected:
        current_time = time.time()
        if current_time - last_alarm_time > 3: # Trigger audio every 3 seconds
            speak("Warning! Fire accident detected in the kitchen!")
            last_alarm_time = current_time

    cv2.imshow("Visual Fire Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()