import sys
import time
import cv2
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QPushButton  
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from kansel_ui import KanselMainWindow
from yolo_detector import YOLODetector
from face_recognition_utils import verify_identity, detect_gaze_deviation
from voice_activity_detector import VoiceActivityDetector
from browser_logger import BrowserLogger
from light_noise_analysis import LightNoiseAnalyzer
from report_generator import ReportGenerator
from email_alert import send_malpractice_email, send_otp_email, generate_otp


class ProctoringSession(QThread):
    status_updated = pyqtSignal(str)
    session_ended = pyqtSignal(str)
    frame_ready = pyqtSignal(QPixmap)

    def __init__(self, candidate_name, candidate_email, reference_image_path):
        super().__init__()
        self.candidate_name = candidate_name
        self.candidate_email = candidate_email
        self.reference_image_path = reference_image_path
        self.session_active = True

    def run(self):
        try:
            cap = cv2.VideoCapture(0)
            ret, live_frame = cap.read()
            if not ret or not verify_identity(self.reference_image_path, live_frame):
                self.status_updated.emit("❌ Identity verification failed. Ending exam.")
                cap.release()
                self.session_ended.emit("Verification failed.")
                return

            self.status_updated.emit("✅ Identity verified. Starting proctoring...")
            yolo = YOLODetector()
            voice_detector = VoiceActivityDetector()
            light_noise = LightNoiseAnalyzer()
            report = ReportGenerator(self.candidate_name)
            malpractice_details = []
            malpractice_evidence_images = []

            while self.session_active:
                ret, frame = cap.read()
                if not ret:
                    break

                # Emit current frame to UI
                self.send_frame_to_ui(frame)

                # Malpractice detection
                malpractice_objects = yolo.detect_malpractice_objects(frame)
                if malpractice_objects:
                    for obj in malpractice_objects:
                        msg = f"Malpractice Object Detected: {obj['label']}"
                        report.add_event(msg, frame)
                        malpractice_details.append(msg)
                        malpractice_evidence_images.append(f"report_images/event_{len(report.events)}.jpg")
                    self.status_updated.emit("❌ Malpractice detected. Terminating exam.")
                    self.session_active = False
                    break

                if yolo.detect_multiple_persons(frame):
                    msg = "Multiple persons detected"
                    report.add_event(msg, frame)
                    malpractice_details.append(msg)
                    malpractice_evidence_images.append(f"report_images/event_{len(report.events)}.jpg")
                    self.status_updated.emit("❌ Malpractice detected. Terminating exam.")
                    self.session_active = False
                    break

                # Gaze
                gaze_deviated, direction, no_face, blink = detect_gaze_deviation(frame)
                if no_face:
                    self.status_updated.emit("⚠️ No face detected.")
                elif gaze_deviated:
                    report.add_gaze_event(time.strftime("%Y-%m-%d %H:%M:%S"), direction)
                    self.status_updated.emit(f"👀 Gaze Deviation: {direction}")

                # Voice
                if voice_detector.is_voice_detected():
                    report.add_voice_event(time.strftime("%Y-%m-%d %H:%M:%S"))
                    self.status_updated.emit("🎤 Voice Detected!")

                # Lighting/Noise
                light, noise = light_noise.analyze(frame)
                if light < 50:
                    self.status_updated.emit("⚠️ Low lighting.")
                if noise > 95:
                    self.status_updated.emit("⚠️ High noise level.")

            cap.release()
            voice_detector.close()

            report_path = report.generate_report()
            send_malpractice_email(
                self.candidate_name,
                report_path,
                "\n".join(malpractice_details) or "No major violations.",
                malpractice_evidence_images
            )
            self.status_updated.emit("✅ Session ended. Report emailed.")
            self.session_ended.emit("Malpractice detected. Exam ended.")

        except Exception as e:
            self.status_updated.emit(f"❌ Error occurred: {str(e)}")
            self.session_ended.emit("Error")

    def send_frame_to_ui(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.frame_ready.emit(QPixmap.fromImage(qt_img))


class App(KanselMainWindow):
    def __init__(self):
        super().__init__()
        self.candidate_name = ""
        self.reference_image_path = ""
        self.candidate_email = ""
        self.proctor_thread = None

        # override the button behavior
        self.candidate_page.verify_and_continue = self.verify_and_continue
        self.two_fa_page.navigate_back = self.show_exam_page

        # Add status + video to exam page
        self.status_label = QLabel("Monitoring...")
        self.status_label.setStyleSheet("color: green; font-size: 14px;")
        self.video_label = QLabel()
        self.exam_page.layout().insertWidget(0, self.status_label)
        self.exam_page.layout().insertWidget(1, self.video_label)
        self.end_exam_button.clicked.connect(self.end_exam)



    def verify_and_continue(self, name, photo_path):
        self.candidate_name = name
        self.reference_image_path = photo_path
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret or not verify_identity(photo_path, frame):
            QMessageBox.critical(self, "Verification Failed", "Face did not match the reference image.")
            return
        QMessageBox.information(self, "Identity Verified", "Face verified successfully.")
        self.show_2fa_page()

    def show_exam_page(self):
        self.candidate_email = self.two_fa_page.email_input.text().strip()
        self.start_proctoring()
        super().show_exam_page()

    def start_proctoring(self):
        self.proctor_thread = ProctoringSession(
            self.candidate_name,
            self.candidate_email,
            self.reference_image_path
        )
        self.proctor_thread.status_updated.connect(self.update_status)
        self.proctor_thread.session_ended.connect(self.finish_proctoring)
        self.proctor_thread.frame_ready.connect(self.video_label.setPixmap)
        self.proctor_thread.start()

    def update_status(self, msg):
        print("[Status]:", msg)
        self.status_label.setText(msg)

    def finish_proctoring(self, result):
        QMessageBox.information(self, "Session Complete", f"{result}")
        self.show_home_page()

    def end_exam(self):
        if self.proctor_thread:
            self.proctor_thread.session_active = False
            self.status_label.setText("Ending session...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
