import numpy as np
import cv2

# 1. FATIGUE DETECTOR (Eye Aspect Ratio - EAR)
# This checks how open your eyes are.
# If the vertical distance is small compared to horizontal, the eye is closed.
def calculate_ear(eye_landmarks, all_landmarks):
    # Get coordinates for specific eye points
    # P1, P4 are the corners (horizontal)
    # P2, P6 and P3, P5 are the eyelids (vertical)
    
    # We use specific indexes from MediaPipe Face Mesh
    # These numbers map to specific dots on the eye
    p2_y = all_landmarks[eye_landmarks[1]].y
    p6_y = all_landmarks[eye_landmarks[5]].y
    p3_y = all_landmarks[eye_landmarks[2]].y
    p5_y = all_landmarks[eye_landmarks[4]].y
    
    p1_x = all_landmarks[eye_landmarks[0]].x
    p4_x = all_landmarks[eye_landmarks[3]].x
    
    # Calculate vertical distances
    vertical_1 = abs(p2_y - p6_y)
    vertical_2 = abs(p3_y - p5_y)
    
    # Calculate horizontal distance
    horizontal = abs(p1_x - p4_x)
    
    # The Math: Average vertical / horizontal
    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return ear

# 2. DISTRACTION DETECTOR (Head Pose)
# We use the "Perspective-n-Point" (PnP) algorithm to find the head's 3D angle.
def get_head_pose(landmarks, img_w, img_h):
    # Define the 3D model points of a generic face (standard face geometry)
    # Nose tip, Chin, Left Eye corner, Right Eye corner, Mouth corners
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corner
        (-150.0, -150.0, -125.0),    # Left Mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ])

    # Get the 2D pixel coordinates of these same points from your face mesh
    # MediaPipe indexes: 1=Nose, 152=Chin, 263=LeftEye, 33=RightEye, 291=LeftMouth, 61=RightMouth
    image_points = np.array([
        (landmarks[1].x * img_w, landmarks[1].y * img_h),
        (landmarks[152].x * img_w, landmarks[152].y * img_h),
        (landmarks[263].x * img_w, landmarks[263].y * img_h),
        (landmarks[33].x * img_w, landmarks[33].y * img_h),
        (landmarks[291].x * img_w, landmarks[291].y * img_h),
        (landmarks[61].x * img_w, landmarks[61].y * img_h)
    ], dtype="double")

    # Camera internals (approximate)
    focal_length = img_w
    center = (img_w / 2, img_h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")
    
    dist_coeffs = np.zeros((4, 1)) # Assuming no lens distortion

    # Solve PnP: Matches the 2D dots to the 3D model to find angle
    (success, rotation_vector, translation_vector) = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )

    # Convert rotation vector to readable angles (Pitch, Yaw, Roll)
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    pose_mat = cv2.hconcat((rotation_matrix, translation_vector))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
    
    pitch, yaw, roll = [angle[0] for angle in euler_angles]
    return pitch, yaw, roll

# 3. POSTURE DETECTOR
# Checks if the nose is too far forward compared to shoulders (Slouching)
def check_posture(pose_landmarks):
    # Get Left and Right Shoulder Y-coordinates
    # MediaPipe Pose Index: 11=Left Shoulder, 12=Right Shoulder
    left_shoulder_y = pose_landmarks[11].y
    right_shoulder_y = pose_landmarks[12].y
    
    # Get Nose Y-coordinate (Index 0)
    nose_y = pose_landmarks[0].y
    
    # Calculate simple neck offset
    shoulder_midpoint = (left_shoulder_y + right_shoulder_y) / 2
    offset = shoulder_midpoint - nose_y
    
    return offset