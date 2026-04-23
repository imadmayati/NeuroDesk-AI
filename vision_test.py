import cv2  # The library that accesses the webcam (OpenCV)
import mediapipe as mp  # The Google AI library for face/body detection

# 1. Initialize MediaPipe Drawing & Solutions
# These are helper tools to draw the lines and dots on your face
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Initialize Face Mesh (for fatigue/distraction) and Pose (for posture)
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose

# 2. Setup Webcam Access
# The number '0' usually refers to the default webcam on your laptop
cap = cv2.VideoCapture(0)

# 3. Configure the AI Models
# min_detection_confidence=0.5 means the AI needs to be 50% sure it sees a face to track it
with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh, \
     mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as pose:

    print("Camera starting... Press 'q' to quit.")

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # 4. Image Processing
        # To improve performance, mark the image as not writeable to pass by reference
        image.flags.writeable = False
        # Convert the color space from BGR (OpenCV default) to RGB (MediaPipe requirement)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 5. Run the AI Inference
        # This is where the magic happens: detect the face and body
        face_results = face_mesh.process(image)
        pose_results = pose.process(image)

        # Draw the annotations on the image
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # 6. Draw Face Mesh (The "Net" over your face)
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
                
                # Draw the eyes/iris contours (useful for fatigue tracking later)
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_iris_connections_style())

        # 7. Draw Pose Landmarks (Shoulders and body)
        if pose_results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image,
                pose_results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

        # 8. Show the Window
        # Flip the image horizontally for a selfie-view display
        cv2.imshow('FocusFlow Vision Test', cv2.flip(image, 1))

        # Break the loop if 'q' is pressed
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()