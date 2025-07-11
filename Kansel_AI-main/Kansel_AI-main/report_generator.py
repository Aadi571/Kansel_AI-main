from fpdf import FPDF
import os
import cv2

class ReportGenerator:
    def __init__(self, candidate_name):
        self.candidate_name = candidate_name
        self.events = []  # (description, image_path)
        self.image_folder = "report_images"
        os.makedirs(self.image_folder, exist_ok=True)

        self.gaze_events = []   # (timestamp, reason)
        self.voice_events = []  # timestamp only

    def add_event(self, description, frame):
        if frame is not None:
            image_path = os.path.join(self.image_folder, f"event_{len(self.events)+1}.jpg")
            cv2.imwrite(image_path, frame)
            self.events.append((description, image_path))
        else:
            self.events.append((description, None))

    def add_gaze_event(self, timestamp, reason):
        self.gaze_events.append((timestamp, reason))

    def add_voice_event(self, timestamp):
        self.voice_events.append(timestamp)

    def generate_report(self):
        pdf = FPDF()
        
        # ----------------- Front Page ------------------
        pdf.add_page()
        cover_path = "Report front Page.png"  # Make sure this file exists in the working directory
        if os.path.exists(cover_path):
            pdf.image(cover_path, x=0, y=0, w=210, h=297)
        else:
            pdf.set_font("Arial", 'B', 24)
            pdf.cell(0, 100, "Kansel AI Proctoring App", ln=True, align='C')
            pdf.set_font("Arial", '', 14)
            pdf.cell(0, 10, f"Candidate: {self.candidate_name}", ln=True, align='C')

        # ----------------- Main Report ------------------
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Proctoring Report for Candidate: {self.candidate_name}", ln=True)
        pdf.ln(8)

        # Malpractice Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Malpractice Events", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0)
        
        if not self.events:
            pdf.cell(0, 10, "No significant malpractice events detected during the exam.", ln=True)
        else:
            for i, (desc, img_path) in enumerate(self.events, 1):
                pdf.multi_cell(0, 10, f"{i}. {desc}")
                if img_path:
                    try:
                        pdf.image(img_path, w=100)
                        pdf.ln(5)
                    except:
                        pdf.cell(0, 10, "[Image could not be loaded]", ln=True)

        pdf.ln(5)

        # Gaze Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, f"Gaze Detection Summary (Total {len(self.gaze_events)} times):", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0)

        if not self.gaze_events:
            pdf.cell(0, 10, "No gaze deviation detected.", ln=True)
        else:
            for i, (timestamp, reason) in enumerate(self.gaze_events, 1):
                pdf.cell(0, 10, f"{i}. At {timestamp}: {reason}", ln=True)

        pdf.ln(5)

        # Voice Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, f"Voice Detection Summary (Total {len(self.voice_events)} times):", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0)

        if not self.voice_events:
            pdf.cell(0, 10, "No voice activity detected.", ln=True)
        else:
            for i, timestamp in enumerate(self.voice_events, 1):
                pdf.cell(0, 10, f"{i}. Voice detected at {timestamp}", ln=True)

        # Save Report
        report_path = f"proctoring_report_{self.candidate_name}.pdf"
        pdf.output(report_path)
        return report_path
