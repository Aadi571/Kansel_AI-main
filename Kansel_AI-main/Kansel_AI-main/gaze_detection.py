import cv2
import mediapipe as mp

class GazeDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def get_gaze_direction(self, frame):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(img_rgb)

        if not results.multi_face_landmarks:
            return None

        h, w, _ = frame.shape
        landmarks = results.multi_face_landmarks[0].landmark

        # Iris landmarks
        left_iris = landmarks[474]
        right_iris = landmarks[469]

        # Horizontal eye landmarks
        left_eye_outer = landmarks[33]
        left_eye_inner = landmarks[133]
        right_eye_inner = landmarks[362]
        right_eye_outer = landmarks[263]

        # Vertical eye landmarks
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]

        # Convert to pixel coordinates
        left_iris_x = int(left_iris.x * w)
        right_iris_x = int(right_iris.x * w)
        left_iris_y = int(left_iris.y * h)
        right_iris_y = int(right_iris.y * h)

        left_outer_x = int(left_eye_outer.x * w)
        left_inner_x = int(left_eye_inner.x * w)
        right_outer_x = int(right_eye_outer.x * w)
        right_inner_x = int(right_eye_inner.x * w)

        left_top_y = int(left_eye_top.y * h)
        left_bottom_y = int(left_eye_bottom.y * h)
        right_top_y = int(right_eye_top.y * h)
        right_bottom_y = int(right_eye_bottom.y * h)

        # Horizontal ratios
        left_eye_ratio = (left_iris_x - left_outer_x) / max((left_inner_x - left_outer_x), 1)
        right_eye_ratio = (right_iris_x - right_inner_x) / max((right_outer_x - right_inner_x), 1)
        horizontal_ratio = (left_eye_ratio + right_eye_ratio) / 2

        # Vertical ratios
        left_eye_vertical = (left_iris_y - left_top_y) / max((left_bottom_y - left_top_y), 1)
        right_eye_vertical = (right_iris_y - right_top_y) / max((right_bottom_y - right_top_y), 1)
        vertical_ratio = (left_eye_vertical + right_eye_vertical) / 2

        # Determine direction
        if horizontal_ratio < 0.35:
            return "LOOKING_LEFT"
        elif horizontal_ratio > 0.65:
            return "LOOKING_RIGHT"
        elif vertical_ratio < 0.35:
            return "LOOKING_UP"
        elif vertical_ratio > 0.65:
            return "LOOKING_DOWN"
        else:
            return "LOOKING_FORWARD"
