# activity_logger.py

from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

class ActivityLogger:
    def __init__(self, candidate_name):
        self.candidate_name = candidate_name
        self.logs = []

    def log(self, event_type, details):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"{timestamp} - {event_type}: {details}")

    def generate_report(self):
        filename = f"{self.candidate_name}_proctoring_report.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 12)
        c.drawString(30, height - 40, f"Proctoring Report for {self.candidate_name}")
        y = height - 80
        for log_entry in self.logs:
            c.drawString(30, y, log_entry)
            y -= 15
            if y < 40:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - 40
        c.save()
        return os.path.abspath(filename)
