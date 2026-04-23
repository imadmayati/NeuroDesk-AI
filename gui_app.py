import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import sys
import cv2
import mediapipe as mp
import numpy as np
import time
import winsound
import urllib.request  # Standard internet tool
import screen_brightness_control as sbc
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import focus_utils
import logger
import dashboard

# --- CONFIGURATION (HARDCODED) ---
IPHONE_WEBHOOK_URL = "https://api.pushcut.io/9xNWvZoaoorQYcx1sBHJr/notifications/TurnOnFocus"
FOCUS_MODE_TRIGGER_TIME = 3.0  # 3 Seconds for FAST testing

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    update_status_signal = pyqtSignal(str, str)

    def run(self):
        # Initialize Database
        logger.init_db()
        
        # Initialize Brightness
        original_brightness = 100
        try:
            current = sbc.get_brightness()
            if current: original_brightness = current[0]
        except: pass

        # AI Models
        mp_face_mesh = mp.solutions.face_mesh
        mp_pose = mp.solutions.pose

        LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144] 
        RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
        
        cap = cv2.VideoCapture(0)
        
        # Logic Variables
        distraction_start_time = None 
        focus_start_time = None
        is_focus_mode_active = False
        is_dimmed = False

        with mp_face_mesh.FaceMesh(refine_landmarks=True) as face_mesh, \
             mp_pose.Pose() as pose:

            while cap.isOpened():
                ret, cv_img = cap.read()
                if not ret: continue

                cv_img.flags.writeable = False
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, c = rgb_image.shape
                
                face_results = face_mesh.process(rgb_image)
                pose_results = pose.process(rgb_image)

                current_status = "FOCUSED"
                color_hex = "green"
                
                # --- 1. DETECTION ---
                if face_results.multi_face_landmarks:
                    for face_landmarks in face_results.multi_face_landmarks:
                        lm = face_landmarks.landmark
                        left_ear = focus_utils.calculate_ear(LEFT_EYE_IDX, lm)
                        right_ear = focus_utils.calculate_ear(RIGHT_EYE_IDX, lm)
                        avg_ear = (left_ear + right_ear) / 2.0
                        pitch, yaw, roll = focus_utils.get_head_pose(lm, w, h)

                        if avg_ear < 0.22:
                            current_status = "FATIGUE"
                        elif abs(yaw) > 20 or abs(pitch) > 15:
                            current_status = "DISTRACTED"

                if pose_results.pose_landmarks:
                    offset = focus_utils.check_posture(pose_results.pose_landmarks.landmark)
                    if offset < 0.20 and current_status == "FOCUSED":
                        current_status = "BAD POSTURE"

                # --- 2. LOGIC & ACTUATION ---
                if current_status != "FOCUSED":
                    # BAD BEHAVIOR
                    focus_start_time = None # Reset focus timer
                    is_focus_mode_active = False # Reset iPhone trigger so it can fire again later
                    
                    if distraction_start_time is None:
                        distraction_start_time = time.time()
                    
                    elapsed_time = time.time() - distraction_start_time
                    
                    if elapsed_time > 5.0: # 5 seconds distraction allowance
                        color_hex = "red"
                        if not is_dimmed:
                             # DIM SCREEN
                             try:
                                 sbc.set_brightness(20)
                                 is_dimmed = True
                                 winsound.Beep(500, 200)
                             except: pass
                    else:
                        color_hex = "orange"
                        
                else:
                    # GOOD BEHAVIOR (FOCUSED)
                    distraction_start_time = None
                    
                    # Restore Screen
                    if is_dimmed:
                        try:
                            sbc.set_brightness(original_brightness)
                            is_dimmed = False
                        except: pass
                    
                    color_hex = "green"
                    
                    # CHECK FOCUS TIMER FOR iPHONE
                    if focus_start_time is None:
                        focus_start_time = time.time()
                    
                    focus_duration = time.time() - focus_start_time
                    
                    # TRIGGER iPHONE
                    if focus_duration > FOCUS_MODE_TRIGGER_TIME:
                        # Only trigger if we haven't already done it this session
                        if not is_focus_mode_active: 
                            print(f"!!! TRIGGERING IPHONE NOW ({focus_duration:.1f}s) !!!")
                            
                            # --- DIRECT IPHONE CALL (No external file) ---
                            try:
                                with urllib.request.urlopen(IPHONE_WEBHOOK_URL, timeout=2) as response:
                                    if response.getcode() == 200:
                                        print(">>> IPHONE SUCCESS <<<")
                                        winsound.Beep(1000, 100)
                                        winsound.Beep(2000, 300) # Victory Sound
                                        is_focus_mode_active = True # Stop spamming
                                        current_status = "IPHONE SYNCED" # Show on GUI
                                        color_hex = "#00FFFF" # Cyan Color
                            except Exception as e:
                                print(f"iPhone Error: {e}")
                                is_focus_mode_active = True # Stop retrying to avoid lag

                # Log Data
              # --- LOG DATA ---
                if current_status != "IPHONE SYNCED":
                    logger.log_data(current_status, 0, 0)

                # Update GUI
                qt_image = QImage(rgb_image.data, w, h, w * c, QImage.Format.Format_RGB888)
                self.change_pixmap_signal.emit(qt_image)
                self.update_status_signal.emit(current_status, color_hex)

    def stop(self):
        self.terminate()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusFlow - Final Integrated")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #2b2b2b;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # HEADER
        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: white; padding: 10px; background-color: #444; border-radius: 5px;")
        self.layout.addWidget(self.status_label)

        # VIDEO
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.video_label)

        # BUTTONS
        self.button_layout = QHBoxLayout()
        
        self.btn_report = QPushButton("Generate Report")
        self.btn_report.setFont(QFont("Arial", 14))
        self.btn_report.setStyleSheet("background-color: #007bff; color: white; padding: 15px; border-radius: 5px;")
        self.btn_report.clicked.connect(self.generate_report)
        self.button_layout.addWidget(self.btn_report)

        self.btn_quit = QPushButton("Exit System")
        self.btn_quit.setFont(QFont("Arial", 14))
        self.btn_quit.setStyleSheet("background-color: #dc3545; color: white; padding: 15px; border-radius: 5px;")
        self.btn_quit.clicked.connect(self.close)
        self.button_layout.addWidget(self.btn_quit)

        self.layout.addLayout(self.button_layout)

        # Start Thread
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.update_status_signal.connect(self.update_status)
        self.thread.start()

    def update_image(self, qt_image):
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def update_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: white; background-color: {color}; padding: 10px; border-radius: 5px;")

    def generate_report(self):
        self.status_label.setText("GENERATING REPORT...")
        try:
            dashboard.generate_report()
            self.status_label.setText("REPORT SAVED!")
        except Exception as e:
            print(f"Report Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())