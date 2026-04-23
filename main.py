import cv2
import mediapipe as mp
import time
import focus_utils
import actuators
import logger  # <--- NEW IMPORT

# Initialize Systems
actuators.init()
logger.init_db()  # <--- NEW: Create the CSV file

mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose

# CONSTANTS
EAR_THRESHOLD = 0.22
PITCH_THRESHOLD = 15
YAW_THRESHOLD = 20
POSTURE_THRESHOLD = 0.20

# TIMING VARIABLES FOR LOGGING
last_log_time = time.time()
LOG_INTERVAL = 1.0  # Log data once every 1 second

# Eye Indexes
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144] 
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

cap = cv2.VideoCapture(0)

print("System Active. Data is being logged.")

with mp_face_mesh.FaceMesh(refine_landmarks=True) as face_mesh, \
     mp_pose.Pose() as pose:

    while cap.isOpened():
        success, image = cap.read()
        if not success: continue

        # Performance optimization
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, c = image.shape
        
        face_results = face_mesh.process(image)
        pose_results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Default Values
        status = "FOCUSED"
        color = (0, 255, 0)
        avg_ear = 0.0
        yaw = 0.0
        offset = 0.0

        # 1. DETECT FATIGUE & DISTRACTION
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                lm = face_landmarks.landmark
                
                left_ear = focus_utils.calculate_ear(LEFT_EYE_IDX, lm)
                right_ear = focus_utils.calculate_ear(RIGHT_EYE_IDX, lm)
                avg_ear = (left_ear + right_ear) / 2.0
                
                pitch, yaw, roll = focus_utils.get_head_pose(lm, w, h)

                if avg_ear < EAR_THRESHOLD:
                    status = "FATIGUE"
                    color = (0, 0, 255)
                    actuators.trigger_fatigue_alert()
                elif abs(yaw) > YAW_THRESHOLD or abs(pitch) > PITCH_THRESHOLD:
                    status = "DISTRACTED"
                    color = (0, 165, 255)
                    actuators.trigger_distraction_alert()
                    actuators.reset_screen()

        # 2. DETECT POSTURE
        if pose_results.pose_landmarks:
            offset = focus_utils.check_posture(pose_results.pose_landmarks.landmark)
            if offset < POSTURE_THRESHOLD and status == "FOCUSED":
                status = "BAD POSTURE"
                color = (0, 255, 255)
                actuators.trigger_distraction_alert()

        # 3. RESET SCREEN IF FOCUSED
        if status == "FOCUSED":
            actuators.reset_screen()

        # ---------------------------------------------------------
        # NEW: DATA LOGGING (Once per second)
        # ---------------------------------------------------------
        if time.time() - last_log_time > LOG_INTERVAL:
            logger.log_data(status, avg_ear, offset)
            last_log_time = time.time()
            # Flash a small white circle to show data was saved
            cv2.circle(image, (w - 20, 20), 5, (255, 255, 255), -1)

        # Display
        cv2.putText(image, f"Status: {status}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        debug_info = f"EAR: {avg_ear:.2f} | Posture: {offset:.2f}"
        cv2.putText(image, debug_info, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow('FocusFlow Main', image)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            actuators.reset_screen()
            break

cap.release()
cv2.destroyAllWindows()