import face_recognition
import numpy as np
import mediapipe as mp
import cv2

# Identity verification function (unchanged)
def verify_identity(reference_image_path, live_frame, tolerance=0.6):
    ref_image = face_recognition.load_image_file(reference_image_path)
    ref_encodings = face_recognition.face_encodings(ref_image)
    if not ref_encodings:
        return False
    reference_encoding = ref_encodings[0]

    live_encodings = face_recognition.face_encodings(live_frame)
    if not live_encodings:
        return False

    if isinstance(reference_encoding, np.ndarray) and isinstance(live_encodings[0], np.ndarray):
        matches = face_recognition.compare_faces([reference_encoding], live_encodings[0], tolerance=tolerance)
        return matches[0]
    else:
        return False

# Mediapipe initialization
mp_face_mesh = mp.solutions.face_mesh
FACE_MESH = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

def calculate_EAR(landmarks, eye_indices, frame_width, frame_height):
    # Convert normalized landmarks to pixel coordinates
    points = [(int(landmarks.landmark[i].x * frame_width), int(landmarks.landmark[i].y * frame_height)) for i in eye_indices]

    # Compute distances
    def euclidean_dist(a, b):
        return np.linalg.norm(np.array(a) - np.array(b))

    vertical_1 = euclidean_dist(points[1], points[5])
    vertical_2 = euclidean_dist(points[2], points[4])
    horizontal = euclidean_dist(points[0], points[3])

    EAR = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return EAR

def detect_gaze_deviation(frame, ear_threshold=0.25):
    if frame is None:
        return False, None, True, False  # no_face=True

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = FACE_MESH.process(frame_rgb)

    if not results.multi_face_landmarks:
        return False, None, True, False  # no_face=True

    face_landmarks = results.multi_face_landmarks[0]
    h, w, _ = frame.shape

    # Indices for blink detection
    left_eye_indices = [33, 160, 158, 133, 153, 144]
    right_eye_indices = [362, 385, 387, 263, 373, 380]

    # Indices for iris center (approximate from MediaPipe)
    left_iris_center_idx = 468
    right_iris_center_idx = 473

    left_EAR = calculate_EAR(face_landmarks, left_eye_indices, w, h)
    right_EAR = calculate_EAR(face_landmarks, right_eye_indices, w, h)
    avg_EAR = (left_EAR + right_EAR) / 2.0
    blink = avg_EAR < ear_threshold

    # Get eye corners
    left_eye_outer = face_landmarks.landmark[33]
    left_eye_inner = face_landmarks.landmark[133]
    right_eye_outer = face_landmarks.landmark[362]
    right_eye_inner = face_landmarks.landmark[263]

    # Get iris centers
    left_iris = face_landmarks.landmark[left_iris_center_idx]
    right_iris = face_landmarks.landmark[right_iris_center_idx]

    # Calculate relative iris position (0 = left, 1 = right)
    left_ratio = (left_iris.x - left_eye_outer.x) / (left_eye_inner.x - left_eye_outer.x)
    right_ratio = (right_iris.x - right_eye_outer.x) / (right_eye_inner.x - right_eye_outer.x)

    # Average ratio
    avg_ratio = (left_ratio + right_ratio) / 2.0

    # Gaze direction thresholds
    if avg_ratio < 0.35:
        direction = "Looking Left"
    elif avg_ratio > 0.65:
        direction = "Looking Right"
    elif (left_iris.y + right_iris.y) / 2 > left_eye_outer.y + 0.02:
        direction = "Looking Down"
    else:
        direction = "Looking Center"

    # Gaze deviation if not looking center and not blinking
    gaze_deviated = direction != "Looking Center" and not blink

    return gaze_deviated, direction, False, blink  # no_face=False
