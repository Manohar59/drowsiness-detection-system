# 🚗 Driver Drowsiness Detection System

This project implements a real-time driver drowsiness detection system using computer vision techniques. The system monitors the driver’s eye state and alerts when signs of drowsiness are detected, helping to reduce road accidents caused by fatigue.

---

## 📌 Features

- 🔍 Real-time webcam monitoring
- 👁️ Eye blink detection using facial landmarks
- 😴 Drowsiness alert system (sound or visual warning)
- 📊 Live status display (e.g., Drowsy / Alert)
- 🧠 OpenCV + Dlib / Mediapipe-based facial detection

---

## 🛠️ Technologies Used

- Python
- OpenCV
- Dlib or Mediapipe
- imutils
- NumPy
- Pygame (for sound alerts)

---

## 📷 How It Works

1. Webcam captures the driver's face.
2. Facial landmarks are used to locate the eyes.
3. Eye Aspect Ratio (EAR) is calculated:
   - If EAR remains low for several frames → driver is likely drowsy.
4. If drowsiness is detected:
   - An alarm is triggered to alert the driver.

---

## 🔧 Installation

```bash
git clone https://github.com/your-username/drowsiness-detection.git
cd drowsiness-detection
pip install -r requirements.txt
python detect_drowsiness.py
├── detect_drowsiness.py         # Main script
├── shape_predictor_68.dat       # Facial landmark model
├── requirements.txt
├── alarm.wav                    # Alert sound
├── README.md
