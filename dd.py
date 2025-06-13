import cv2
import numpy as np
import dlib
from imutils import face_utils
import os
import pygame
import time
import pyttsx3
import tkinter as tk
from PIL import Image, ImageTk
import uuid

# -- Configuration --
MODEL_PATH        = "shape_predictor_68_face_landmarks.dat"
SLEEP_FILE        = "audio_alert.wav"
DROWSY_FILE       = "dddd.wav"
EAR_THRESH_OPEN   = 0.25
EAR_THRESH_DROWSY = 0.21
FRAME_THRESH      = 6

# Verify required files
required_files = [MODEL_PATH, SLEEP_FILE, DROWSY_FILE]
for f in required_files:
    if not os.path.exists(f):
        raise FileNotFoundError(f"Required file missing: {f}")

# Initialize Pygame
pygame.init()  # Initialize all Pygame modules, including video system
pygame.mixer.init()  # Initialize mixer for audio
sleep_sound = pygame.mixer.Sound(SLEEP_FILE)
drowsy_sound = pygame.mixer.Sound(DROWSY_FILE)
alarm_channel = None

# Initialize TTS
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

# Setup camera and models
cap = cv2.VideoCapture(0)
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

# State tracking
sleep_count = drowsy_count = active_count = 0
status = "ACTIVE"
active_timer_start = time.time()
total_active_time = 0
last_status_change = time.time()
running = False

def compute(a, b):
    return np.linalg.norm(a - b)

def blinked(a, b, c, d, e, f):
    up = compute(b, d) + compute(c, e)
    down = compute(a, f)
    ratio = up / (2.0 * down)
    if ratio > EAR_THRESH_OPEN:
        return 2
    elif ratio > EAR_THRESH_DROWSY:
        return 1
    return 0

def speak_alert(status):
    try:
        if status == "DROWSY":
            tts_engine.say("Stay alert! You are feeling drowsy")
        elif status == "SLEEPING":
            tts_engine.say("Wake up! You are falling asleep")
        tts_engine.runAndWait()
    except Exception as e:
        print(f"Voice alert error: {e}")

def get_timer_text():
    elapsed = total_active_time
    if status == "ACTIVE":
        elapsed += time.time() - active_timer_start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    return f"{mins:02d}:{secs:02d}"

class DrowsinessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SMART DRIVER ALERT SYSTEM")
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")

        # Video feed
        self.video_label = tk.Label(root, bg="#2c3e50")
        self.video_label.pack(pady=10)

        # Status display
        self.status_label = tk.Label(root, text="Status: ACTIVE", font=("Arial", 16, "bold"),
                                   fg="green", bg="#2c3e50")
        self.status_label.pack()

        # Timer display
        self.timer_label = tk.Label(root, text="Active Time: 00:00", font=("Arial", 14),
                                  fg="white", bg="#2c3e50")
        self.timer_label.pack(pady=10)

        # Control buttons
        self.button_frame = tk.Frame(root, bg="#2c3e50")
        self.button_frame.pack(pady=10)

        self.start_button = tk.Button(self.button_frame, text="Start", font=("Arial", 12),
                                    command=self.start_detection, bg="#27ae60", fg="white",
                                    activebackground="#2ecc71", width=10)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.button_frame, text="Stop", font=("Arial", 12),
                                   command=self.stop_detection, bg="#c0392b", fg="white",
                                   activebackground="#e74c3c", width=10)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.quit_button = tk.Button(self.button_frame, text="Quit", font=("Arial", 12),
                                   command=self.quit_app, bg="#7f8c8d", fg="white",
                                   activebackground="#95a5a6", width=10)
        self.quit_button.pack(side=tk.LEFT, padx=5)

        # Start GUI update loop
        self.update_gui()

    def start_detection(self):
        global running
        running = True

    def stop_detection(self):
        global running
        running = False
        if alarm_channel:
            alarm_channel.stop()

    def quit_app(self):
        global running
        running = False
        if alarm_channel:
            alarm_channel.stop()
        cap.release()
        pygame.mixer.quit()
        pygame.quit()
        self.root.destroy()

    def play_alert_sound(self, sound, alert_status):
        global alarm_channel
        alarm_channel = pygame.mixer.find_channel()
        if alarm_channel:
            # Set callback for when sound finishes
            alarm_channel.set_endevent(pygame.USEREVENT)
            alarm_channel.play(sound)
            # Store the status for the voice alert
            self.current_alert_status = alert_status

    def handle_audio_events(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                # Sound finished, trigger voice alert
                if hasattr(self, 'current_alert_status'):
                    self.root.after(0, lambda: speak_alert(self.current_alert_status))

    def update_gui(self):
        global sleep_count, drowsy_count, active_count, status, active_timer_start, total_active_time, last_status_change, alarm_channel

        if running:
            # Handle audio events only when running
            self.handle_audio_events()

            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = detector(gray)
                
                if len(faces) > 0:
                    face = faces[0]
                    pts = face_utils.shape_to_np(predictor(gray, face))
                    left = blinked(pts[36], pts[37], pts[38], pts[41], pts[40], pts[39])
                    right = blinked(pts[42], pts[43], pts[44], pts[47], pts[46], pts[45])

                    new_status = status
                    if left == 0 and right == 0:
                        sleep_count += 1
                        drowsy_count = active_count = 0
                        if sleep_count >= FRAME_THRESH:
                            new_status = "SLEEPING"
                    elif left == 1 or right == 1:
                        drowsy_count += 1
                        sleep_count = active_count = 0
                        if drowsy_count >= FRAME_THRESH:
                            new_status = "DROWSY"
                    else:
                        active_count += 1
                        sleep_count = drowsy_count = 0
                        if active_count >= FRAME_THRESH:
                            new_status = "ACTIVE"

                    if new_status != status:
                        if status == "ACTIVE":
                            total_active_time += time.time() - active_timer_start
                        if new_status == "ACTIVE":
                            active_timer_start = time.time()
                        
                        if alarm_channel:
                            alarm_channel.stop()
                        
                        if new_status == "SLEEPING":
                            self.play_alert_sound(sleep_sound, "SLEEPING")
                        elif new_status == "DROWSY":
                            self.play_alert_sound(drowsy_sound, "DROWSY")
                        
                        status = new_status
                        last_status_change = time.time()

                    # Draw face box and status
                    x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    color = (0,0,255) if status=="SLEEPING" else (0,255,255) if status=="DROWSY" else (0,255,0)
                    cv2.putText(frame, status, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
                else:
                    cv2.putText(frame, "NO FACE DETECTED", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)

                # Update video feed
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (640, 480))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

                # Update status and timer
                color = "red" if status == "SLEEPING" else "yellow" if status == "DROWSY" else "green"
                self.status_label.configure(text=f"Status: {status}", fg=color)
                self.timer_label.configure(text=f"Active Time: {get_timer_text()}")

        self.root.after(10, self.update_gui)

if __name__ == "__main__":
    root = tk.Tk()
    app = DrowsinessApp(root)
    root.mainloop()