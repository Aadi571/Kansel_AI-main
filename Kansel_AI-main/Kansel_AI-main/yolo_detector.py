import cv2
import numpy as np

class YOLODetector:
    def __init__(self):
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.4

        weights_path = "yolov4.weights"
        config_path = "yolov4.cfg"
        self.net = cv2.dnn.readNet(weights_path, config_path)
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers().flatten()]

        # Load COCO class names
        with open("coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]

        # Malpractice objects we want to detect
        self.malpractice_objects = {"cell phone", "book"}

    def detect(self, frame):
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416,416), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        boxes = []
        confidences = []
        class_ids = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > self.confidence_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x,y,w,h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)

        detections = []
        if isinstance(indices, tuple) or len(indices) == 0:
            return detections

        if isinstance(indices, np.ndarray):
            indices = indices.flatten()
        else:
            indices = np.array(indices).flatten()

        for i in indices:
            label = self.classes[class_ids[i]]
            box = boxes[i]
            confidence = confidences[i]
            detections.append({
                "label": label,
                "box": box,
                "confidence": confidence
            })
        return detections

    def detect_multiple_persons(self, frame):
        # Count number of 'person' detected in the frame
        detections = self.detect(frame)
        person_count = sum(1 for obj in detections if obj["label"] == "person")
        return person_count > 1

    def detect_malpractice_objects(self, frame):
        detections = self.detect(frame)
        malpractice_detected = [obj for obj in detections if obj["label"] in self.malpractice_objects]
        return malpractice_detected
