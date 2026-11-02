# 🍳 Smart Culinary Assistant & Kitchen Safety System

A computer vision–powered smart kitchen management system that combines **AI ingredient detection**, **PPE (Personal Protective Equipment) compliance scanning**, **face recognition–based access control**, and **real-time fire/gas safety monitoring**.

---

## 🌟 Features

| Module | Description |
|---|---|
| 🧑‍🍳 **Smart Chef Assistant** | Detects cooking ingredients via YOLOv5 in real-time, tracks recipe progress, and gives voice feedback |
| 🦺 **PPE Security Scanner** | Verifies staff identity via face recognition, then checks for mask & gloves compliance |
| 🔥 **Visual Fire Detector** | Detects fire in camera feed using HSV colour masking |
| ⚠️ **Arduino Safety Sensor** | Listens for hardware Gas & IR-Fire sensor signals over serial (Arduino) |

---

## 🗂️ Project Structure

```
ppe-detection-project/
├── yolov5/
│   ├── original_final_chef_assistant.py   # Main Smart Chef app
│   ├── standalone_security_scanner.py     # PPE + face recognition scanner
│   ├── standalone_fire_detector.py        # Visual fire detector
│   ├── models/                            # Place your .pt model files here
│   ├── requirements.txt
│   └── ...
├── encode_faces.py                        # Run this first to generate face encodings
├── known_faces/                           # Add face images here (not committed)
├── .env.example                           # Copy to .env and configure
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ppe-detection-project.git
cd ppe-detection-project
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r yolov5/requirements.txt
pip install python-dotenv pyserial face_recognition pyttsx3
```

### 4. Download Model Weights
The `.pt` model files are **not included** in this repository (too large for git).

Place these files in `yolov5/`:
- `kitchen_ppe_vision_v2.pt` — PPE detection model
- `yolov5s.pt` — Base YOLOv5s model

Place this file in `yolov5/models/`:
- `ultimate_brain.pt` — Custom ingredient detection model

> You can train your own models using the datasets in the `dataset_*` folders, or download pretrained weights from [Ultralytics YOLOv5](https://github.com/ultralytics/yolov5).

### 5. Configure Environment Variables
```bash
cp .env.example .env
```
Edit `.env` to set your Arduino COM port:
```
ARDUINO_PORT=COM7   # Change to your actual port (COM3, COM4, etc.)
```

### 6. Encode Known Faces (for Security Scanner)
1. Create subdirectories in `known_faces/` named after each person (e.g., `known_faces/John_Chef/`)
2. Place face images of each person in their folder
3. Run the encoder:
   ```bash
   python encode_faces.py
   ```
   This generates `face_encodings.pkl` locally (not committed — contains biometric data).

---

## 🚀 Running the Applications

### Smart Chef Assistant
```bash
cd yolov5
python original_final_chef_assistant.py
```
- A menu will appear — click a recipe to start
- Point the camera at ingredients in the cooking zone
- The AI will announce each detected ingredient and track your progress

### PPE Security Scanner
```bash
cd yolov5
python standalone_security_scanner.py
```
- Phase 1: Face scan (15 seconds to identify the person)
- Phase 2: PPE check (verifies mask & gloves are worn)

### Visual Fire Detector
```bash
cd yolov5
python standalone_fire_detector.py
```
- Standalone fire detection via colour-based HSV analysis
- Press `q` to quit

---

## 🛡️ Privacy & Security Notes

- **`face_encodings.pkl`** is listed in `.gitignore` — it is **never committed** as it contains biometric face data
- **`known_faces/`** is listed in `.gitignore` — keep face images local only
- The Arduino COM port is now configured via environment variable (`.env`), not hardcoded
- Model weight files (`.pt`) are excluded due to size — see setup instructions above

---

## 🔧 Hardware Requirements (Optional)

For the full gas/fire hardware safety system:
- Arduino Uno/Nano
- MQ-2 or MQ-5 Gas Sensor
- IR Flame Sensor
- Upload the corresponding Arduino sketch (not included) and set `ARDUINO_PORT` in `.env`

---

## 📦 Key Dependencies

- [YOLOv5](https://github.com/ultralytics/yolov5) — Object detection
- [OpenCV](https://opencv.org/) — Video processing & UI
- [face_recognition](https://github.com/ageitgey/face_recognition) — Face identification
- [pyttsx3](https://pypi.org/project/pyttsx3/) — Text-to-speech alerts
- [PyTorch](https://pytorch.org/) — Deep learning backend
- [pyserial](https://pypi.org/project/pyserial/) — Arduino serial communication

---

## 📄 License

This project is licensed under the AGPL-3.0 License (inherited from YOLOv5).
