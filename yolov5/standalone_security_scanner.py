import cv2
import torch
import face_recognition
import pickle
import pyttsx3
import time
import numpy as np
import pathlib

# --- WINDOWS PATH FIX ---
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath
# ------------------------

engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

print("[INFO] Loading YOLOv5 model...")
model = torch.hub.load('ultralytics/yolov5', 'custom', path='kitchen_ppe_vision_v2.pt')

print("[INFO] Loading Face Encodings...")
try:
    with open("face_encodings.pkl", "rb") as f:
        known_data = pickle.load(f)
        known_encodings = known_data["encodings"]
        known_names = known_data["names_roles"]
except FileNotFoundError:
    print("[ERROR] face_encodings.pkl not found!")
    exit()

cap = cv2.VideoCapture(0)

system_state = "FACE_SCAN"
scan_start_time = time.time()
authorized_person = ""
last_voice_time = 0

print("[INFO] Starting Scanner. Press 'q' to quit, 'r' to reset.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    if system_state == "FACE_SCAN":
        elapsed_time = time.time() - scan_start_time
        remaining_time = int(15 - elapsed_time)
        
        cv2.putText(frame, f"Scanning Face... {remaining_time}s", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            color = (0, 0, 255)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
                
                authorized_person = name
                system_state = "PPE_SCAN"
                speak(f"Access Granted. Switching to PPE scan.")
                last_voice_time = time.time()
                break 

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if elapsed_time > 15 and system_state == "FACE_SCAN":
            speak("Entry Denied. 15 seconds elapsed.")
            scan_start_time = time.time() 

    elif system_state == "PPE_SCAN":
        cv2.putText(frame, f"Authorized: {authorized_person} - Checking PPE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        results = model(frame)
        detections = results.pandas().xyxy[0]
        
        has_mask = False
        has_gloves = False

        for index, row in detections.iterrows():
            confidence = row['confidence']
            class_name = str(row['name']).lower()
            
            # ====================================================
            # THE NUCLEAR HACK: EXTREME CONFIDENCE THRESHOLDS
            # ====================================================
            if confidence < 0.60:
                continue # Ignore everything under 60% immediately

            # GLOVES: Raised to an extreme 80% to kill bare-hand glitches
            is_valid_glove = ('glove' in class_name) and (confidence > 0.80)
            
            # MASKS: Raised to an extreme 85% to kill face glitches
            is_valid_mask = ('mask' in class_name and 'without' not in class_name) and (confidence > 0.85)
            
            # BARE FACES: Requires 65%
            is_bare_face = ('without' in class_name or 'no_mask' in class_name) and (confidence > 0.65)

            if is_valid_glove or is_valid_mask or is_bare_face:
                x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                
                box_color = (0, 255, 255) 
                
                if is_bare_face:
                    box_color = (0, 0, 255) # Red for Violations
                elif is_valid_mask:
                    box_color = (255, 0, 0) # Blue for Mask
                    has_mask = True
                elif is_valid_glove:
                    box_color = (255, 255, 255) # White for Gloves
                    has_gloves = True
                    
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                label = f"{class_name} {confidence:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)
                
        if time.time() - last_voice_time > 8:
            if not has_mask or not has_gloves:
                speak("Please wear your blue mask and white gloves.")
            else:
                speak("PPE compliant. You may enter the kitchen.")
            last_voice_time = time.time()

    cv2.imshow("Security Scanner", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'): 
        system_state = "FACE_SCAN"
        scan_start_time = time.time()

cap.release()
cv2.destroyAllWindows()