import cv2
import torch
import pyttsx3
import threading
import pathlib
import numpy as np
import pandas as pd
import sys
import os
import serial  # Required for Arduino communication

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on system environment variables

# --- CRITICAL WINDOWS FIX ---
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

# --- 1. SETUP VOICE ALERTS ---
def speak(text):
    def run():
        try:
            local_engine = pyttsx3.init()
            local_engine.say(text)
            local_engine.runAndWait()
        except RuntimeError:
            pass 
    threading.Thread(target=run, daemon=True).start()

# --- 2. LOAD YOUR CUSTOM MASTER BRAIN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "models", "ultimate_brain.pt")

try:
    print("Loading Custom Master Brain from GitHub... Please wait.")
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=False)
    
    model.conf = 0.25 # type: ignore 
    model.iou = 0.45 # type: ignore
    print("SUCCESS: Master Brain Loaded! 🧠")
    
    print("\n🚨 MY AI BRAIN MEMORIZED THESE EXACT WORDS:", model.names, "\n") # type: ignore
    
except Exception as e:
    print(f"\n❌ CRITICAL ERROR LOADING AI: {e}")
    print("⚠️ Please ensure you have an internet connection so PyTorch can fetch the architecture.")
    sys.exit() 

# --- 3. EMERGENCY SAFETY SYSTEM (ARDUINO LISTENER) ---
emergency_status = "SAFE"

def safety_listener():
    global emergency_status
    try:
        # Arduino port is read from ARDUINO_PORT env variable (set in .env)
        # Default: COM7 — override by setting ARDUINO_PORT in your .env file
        port = os.environ.get('ARDUINO_PORT', 'COM7')
        baud  = int(os.environ.get('ARDUINO_BAUD_RATE', '9600'))
        arduino = serial.Serial(port, baud, timeout=1)
        print("✅ Arduino Safety Sensors Connected (Gas & IR-Fire)!")
        while True:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()
                
                if line in ["FIRE", "GAS", "SAFE"]:
                    # Only trigger voice if a NEW emergency happens
                    if line != "SAFE" and emergency_status != line:
                        speak(f"EMERGENCY WARNING! {line} DETECTED IN KITCHEN! EVACUATE IMMEDIATELY!")
                            
                    emergency_status = line
    except Exception as e:
        print(f"⚠️ Arduino not connected: {e}. Running without hardware sensors.")

# Start the safety listener in the background so it doesn't pause the video
threading.Thread(target=safety_listener, daemon=True).start()

# --- 4. RECIPE DATABASE ---
RECIPES = {
    "Egg Curry": {
        "oil": {"instruction": "normal", "impact": 20},
        "egg": {"instruction": "careful", "impact": 30},
        "onions": {"instruction": "normal", "impact": 20},
        "salt": {"instruction": "normal", "impact": 15},
        "chilli powder": {"instruction": "normal", "impact": 15}
    },
    "Coffee with Sugar": {
        "coffee": {"instruction": "normal", "impact": 50},
        "sugar": {"instruction": "normal", "impact": 50},
        "toned_milk": {"instruction": "normal", "impact": 50}
    },
    "Chicken Masala": {
        "chicken": {"instruction": "normal", "impact": 20},
        "tomato": {"instruction": "normal", "impact": 10},
        "onion": {"instruction": "normal", "impact": 10},
        "garlic": {"instruction": "normal", "impact": 10},
        "cumin": {"instruction": "normal", "impact": 10},
        "turmeric": {"instruction": "normal", "impact": 10},
        "garam masala": {"instruction": "normal", "impact": 10},
        "red chilli": {"instruction": "normal", "impact": 10},
        "bay leaf": {"instruction": "normal", "impact": 10}
    },
    "Vegetable Pasta": {
        "pasta": {"instruction": "normal", "impact": 30},
        "bell pepper": {"instruction": "normal", "impact": 10},
        "carrot": {"instruction": "normal", "impact": 10},
        "broccoli": {"instruction": "normal", "impact": 10},
        "tomato": {"instruction": "normal", "impact": 10},
        "onion": {"instruction": "normal", "impact": 10},
        "garlic": {"instruction": "normal", "impact": 10},
        "black pepper": {"instruction": "normal", "impact": 10}
    },
    "Aloo Gobi": {
        "potato": {"instruction": "normal", "impact": 20},
        "cayliflower": {"instruction": "careful", "impact": 20}, # Matches dataset spelling!
        "tomato": {"instruction": "normal", "impact": 15},
        "onion": {"instruction": "normal", "impact": 15},
        "cumin": {"instruction": "normal", "impact": 10},
        "turmeric": {"instruction": "normal", "impact": 10},
        "garam masala": {"instruction": "normal", "impact": 10}
    }
}

# --- 5. CHEF MONITOR (UI & LOGIC) ---
class ChefMonitor:
    def __init__(self, recipe_name):
        self.recipe_name = recipe_name
        self.required = RECIPES[recipe_name]
        self.added = []

    def check_frame(self, frame, predictions):
        h, w, _ = frame.shape
        
        # Draw the Cooking Zone
        zone = [int(w*0.25), int(h*0.25), int(w*0.75), int(h*0.75)]
        cv2.rectangle(frame, (zone[0], zone[1]), (zone[2], zone[3]), (255, 150, 0), 2)
        cv2.putText(frame, "COOKING ZONE", (zone[0], zone[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 150, 0), 2)

        # Process Predictions
        for index, row in predictions.iterrows():
            label = str(row['name']).lower()
            conf = row['confidence']
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
            
            # Draw the box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Check logic
            if zone[0] < center_x < zone[2] and zone[1] < center_y < zone[3]:
                if label in self.required.keys() and label not in self.added:
                    self.added.append(label)
                    msg = f"Detected {label}. Added to recipe."
                    print(f"\n[AI VOICE] {msg}\n")
                    speak(msg)

        return frame

    def generate_review(self):
        print("\n" + "="*30)
        print("FINAL CULINARY REVIEW")
        print("="*30)
        score = 100
        missing = []
        for item, details in self.required.items():
            if item not in self.added:
                score -= details["impact"]
                missing.append(item)
        
        score = max(0, score)
        print(f"Quality Score: {score}/100")
        if score == 100:
            msg = "Perfect execution! All ingredients were added correctly."
        else:
            msg = f"Cooking complete. You forgot to add: {', '.join(missing)}."
        
        print(msg)
        speak(msg)

# --- 6. MAIN LOOP ---
def main():
    print("\n👨‍🍳 SMART CHEF INITIALIZED")
    
    selected_recipe = None
    selected_video = None

    # --- BUILD THE OPENCV MENU ---
    menu_img = np.zeros((600, 800, 3), dtype=np.uint8) # type: ignore
    menu_img[:] = (40, 40, 40) 

    cv2.putText(menu_img, "SMART CHEF - MAIN MENU", (230, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(menu_img, "Click a recipe to load the video!", (220, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    buttons = [
        (200, 150, 600, 200, "1. Egg Curry", (34, 126, 230)),        
        (200, 220, 600, 270, "2. Coffee with Sugar", (185, 128, 41)),
        (200, 290, 600, 340, "3. Chicken Masala", (96, 174, 39)),
        (200, 360, 600, 410, "4. Vegetable Pasta", (142, 68, 173)),
        (200, 430, 600, 480, "5. Aloo Gobi", (50, 200, 100))
    ]

    for (x1, y1, x2, y2, text, color) in buttons:
        cv2.rectangle(menu_img, (x1, y1), (x2, y2), color, -1)
        cv2.putText(menu_img, text, (x1 + 20, y1 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def menu_click(event, x, y, flags, param):
        nonlocal selected_recipe, selected_video
        if event == cv2.EVENT_LBUTTONDOWN:
            if 200 <= x <= 600: 
                if 150 <= y <= 200:
                    selected_recipe = "Egg Curry"
                    selected_video = "egg_curry.mp4"  
                elif 220 <= y <= 270:
                    selected_recipe = "Coffee with Sugar"
                    selected_video = "video1.mp4"
                elif 290 <= y <= 340:
                    selected_recipe = "Chicken Masala"
                    selected_video = "chicken_video.mp4" 
                elif 360 <= y <= 410:
                    selected_recipe = "Vegetable Pasta"
                    selected_video = "pasta_video.mp4"
                elif 430 <= y <= 480:
                    selected_recipe = "Aloo Gobi"
                    selected_video = "aloo_gobi_video.mp4"

    cv2.namedWindow("Smart Chef Menu")
    cv2.setMouseCallback("Smart Chef Menu", menu_click)

    while selected_recipe is None:
        cv2.imshow("Smart Chef Menu", menu_img)
        key = cv2.waitKey(10) & 0xFF
        if key == 27 or key == ord('q'): 
            break
            
    cv2.destroyWindow("Smart Chef Menu")
    
    if selected_recipe is None:
        print("Menu closed. Exiting application...")
        return

    # --- START THE AI VIDEO PLAYER ---
    print(f"\n🚀 Launching AI Chef for: {selected_recipe}")
    print(f"🎬 Loading Video: {selected_video}...")
    
    monitor = ChefMonitor(selected_recipe)
    cap = cv2.VideoCapture(selected_video) 
    
    frame_count = 0
    skip_frames = 3 
    last_predictions = pd.DataFrame(columns=['name', 'confidence', 'xmin', 'ymin', 'xmax', 'ymax'])
    global emergency_status
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Video Finished.")
            break
            
        frame = cv2.resize(frame, (800, 600))
        h, w, _ = frame.shape
        frame_count += 1
        
        if frame_count % skip_frames == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = model(frame_rgb, size=416) # type: ignore
            last_predictions = results.pandas().xyxy[0]
                
        frame = monitor.check_frame(frame, last_predictions)
        
        # Draw standard UI
        cv2.putText(frame, f"Recipe: {selected_recipe}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_pos = 60
        for req in monitor.required:
            status = "[v]" if req in monitor.added else "[ ]"
            color = (0, 255, 0) if req in monitor.added else (0, 0, 255)
            cv2.putText(frame, f"{status} {req.upper()}", (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_pos += 25

        if not last_predictions.empty and 'name' in last_predictions.columns:
            current_items = last_predictions['name'].unique().tolist()
            if len(current_items) > 0:
                display_text = "SEEING NOW: " + ", ".join(current_items).upper()
                text_color = (0, 255, 255) 
            else:
                display_text = "SEEING NOW: NOTHING"
                text_color = (150, 150, 150) 
        else:
            display_text = "SEEING NOW: NOTHING"
            text_color = (150, 150, 150)
            
        cv2.putText(frame, display_text, (20, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)

        # --- NEW: EMERGENCY UI OVERLAY ---
        if emergency_status == "FIRE":
            cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 255), 15) # Thick Red Border
            cv2.putText(frame, "🔥 FIRE DETECTED! EVACUATE! 🔥", (60, int(h/2)), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 3)
        elif emergency_status == "GAS":
            cv2.rectangle(frame, (0, 0), (w, h), (0, 255, 255), 15) # Thick Yellow Border
            cv2.putText(frame, "💨 GAS LEAK DETECTED! 💨", (100, int(h/2)), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 255, 255), 3)

        cv2.imshow("Custom AI Chef", frame)
        
        if cv2.waitKey(15) & 0xFF == ord('q') or cv2.waitKey(15) & 0xFF == 27: 
            break
            
    monitor.generate_review()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()