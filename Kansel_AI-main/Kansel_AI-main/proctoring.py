import cv2
import datetime
from yolo_detector import YOLODetector
from face_recognition_utils import verify_identity, detect_gaze_deviation
from voice_activity_detector import VoiceActivityDetector
from browser_logger import BrowserLogger
from light_noise_analysis import LightNoiseAnalyzer
from report_generator import ReportGenerator
from email_alert import send_malpractice_email, send_otp_email, generate_otp
import os

def main():
    # === New: ask candidate info at start ===
    candidate_name = input("Enter candidate name: ").strip()
    candidate_email = input("Enter candidate email (for 2FA): ").strip()

    # === New: Send OTP and verify ===
    otp = generate_otp()
    send_otp_email(candidate_email, otp)

    for attempt in range(3):
        user_input = input("Enter the OTP sent to your email: ").strip()
        if user_input == otp:
            print("✅ OTP verified successfully.")
            break
        else:
            print(f"❌ Incorrect OTP. Attempts left: {2 - attempt}")
    else:
        print("🚫 OTP verification failed. Terminating exam.")
        return

    # Ask for candidate reference image path until valid
    while True:
        reference_image_path = input("Enter path to candidate reference photo: ").strip()
        if os.path.isfile(reference_image_path):
            break
        print(f"File '{reference_image_path}' does not exist. Please enter a valid file path.")

    cap = cv2.VideoCapture(0)

    yolo = YOLODetector()
    voice_detector = VoiceActivityDetector()
    browser_logger = BrowserLogger()
    light_noise = LightNoiseAnalyzer()
    report = ReportGenerator(candidate_name)

    # Identity verification at start
    ret, live_frame = cap.read()
    if not ret:
        print("Failed to capture initial frame.")
        cap.release()
        return

    if not verify_identity(reference_image_path, live_frame):
        print("Candidate identity could not be verified. Terminating exam.")
        cap.release()
        return

    print("Identity verified. Starting exam proctoring...")

    malpractice_detected = False
    malpractice_details = []
    malpractice_evidence_images = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        warning_message = None  # To display on screen

        # Detect malpractice objects
        malpractice_objects = yolo.detect_malpractice_objects(frame)
        if malpractice_objects:
            malpractice_detected = True
            for obj in malpractice_objects:
                desc = f"Malpractice Object Detected: {obj['label']}"
                print(desc)
                report.add_event(desc, frame)
                malpractice_details.append(desc)
                malpractice_evidence_images.append(f"report_images/event_{len(report.events)}.jpg")
            break

        # Detect multiple persons
        if yolo.detect_multiple_persons(frame):
            malpractice_detected = True
            desc = "Multiple persons detected"
            print(desc)
            report.add_event(desc, frame)
            malpractice_details.append(desc)
            malpractice_evidence_images.append(f"report_images/event_{len(report.events)}.jpg")
            break

        # === Gaze deviation detection (updated to match new output) ===
        gaze_deviated, direction, no_face, blink = detect_gaze_deviation(frame)
        if no_face:
            warning_message = "Warning: No face detected!"
        elif gaze_deviated:
            reason = direction if direction else "Looking away"
            warning_message = f"Warning: Gaze deviation - {reason}"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report.add_gaze_event(timestamp, reason)

        # === Improved Voice detection ===
        if voice_detector.is_voice_detected():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report.add_voice_event(timestamp)
            warning_message = "Warning: Voice detected!"

        # === Light and noise check (on-screen warning) ===
        light, noise = light_noise.analyze(frame)
        if light < 50:
            warning_message = "Warning: Low lighting!"
        elif noise > 95 and voice_detector.is_voice_detected():
            warning_message = "Warning: High noise!"
        elif noise > 110:
            warning_message = "Warning: Very high noise!"

        # === Display warning message if any ===
        """if warning_message:
            cv2.putText(frame, warning_message, (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)"""

        # Display frame with info, quit on 'q'
        cv2.imshow("Proctoring", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    voice_detector.close()
    cv2.destroyAllWindows()

    # Generate report
    report_path = report.generate_report()

    # Send email whether malpractice or not
    send_malpractice_email(
        candidate_name,
        report_path,
        "\n".join(malpractice_details) or "No major violations.",
        malpractice_evidence_images
    )

    print("Exam session ended.")

if __name__ == "__main__":
    main()
