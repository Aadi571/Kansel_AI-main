from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QVBoxLayout, QStackedLayout, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import sys
import random
from email_alert import send_otp_email, generate_otp  # ✅ ADDED

class LogoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 300)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setPixmap(QPixmap("Logo1.png").scaled(
            220, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

class HomePage(QWidget):
    def __init__(self, navigate_to_candidate, navigate_to_project):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(30)

        title = QLabel("Kansel AI Proctoring")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet("color: #003366;")

        subtitle = QLabel("AI powered online exam supervision")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #5a7bbf;")

        start_button = QPushButton("Start Proctoring")
        start_button.setCursor(Qt.PointingHandCursor)
        start_button.setMinimumHeight(50)
        start_button.setStyleSheet("""
            QPushButton {
                background-color: #004aad;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                padding-left: 40px;
                padding-right: 40px;
            }
        """)
        start_button.clicked.connect(navigate_to_candidate)

        project_button = QPushButton("Project Details")
        project_button.setCursor(Qt.PointingHandCursor)
        project_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #003366;
                font-size: 14px;
                text-decoration: underline;
                border: none;
            }
            QPushButton:hover {
                color: #1a73e8;
            }
        """)
        project_button.clicked.connect(navigate_to_project)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)
        layout.addWidget(start_button)
        layout.addSpacing(15)
        layout.addWidget(project_button)
        layout.addStretch()
        self.setLayout(layout)

class CandidatePage(QWidget):
    def __init__(self, verify_and_continue, navigate_back):
        super().__init__()
        self.verify_and_continue = verify_and_continue
        self.navigate_back = navigate_back
        self.photo_path = ""

        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(60, 40, 60, 40)

        title = QLabel("Candidate Identity Verification")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #003366;")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")
        self.name_input.setMinimumHeight(40)
        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
                background-color: white;
            }
        """)

        self.upload_button = QPushButton("Upload Reference Photo")
        self.upload_button.setMinimumHeight(40)
        self.upload_button.setCursor(Qt.PointingHandCursor)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #004aad;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        self.upload_button.clicked.connect(self.upload_photo)

        self.verify_button = QPushButton("Verify Identity")
        self.verify_button.setMinimumHeight(40)
        self.verify_button.setCursor(Qt.PointingHandCursor)
        self.verify_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.verify_button.clicked.connect(self.verify_clicked)

        self.back_button = QPushButton("← Back")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setFixedWidth(100)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #003366;
                font-size: 13px;
                text-decoration: underline;
                border: none;
            }
            QPushButton:hover {
                color: #1a73e8;
            }
        """)
        self.back_button.clicked.connect(self.navigate_back)

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(self.name_input)
        layout.addWidget(self.upload_button)
        layout.addWidget(self.verify_button)
        layout.addStretch()
        layout.addWidget(self.back_button, alignment=Qt.AlignLeft)
        self.setLayout(layout)

    def upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Reference Photo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.photo_path = path
            QMessageBox.information(self, "Photo Selected", f"Photo loaded from:\n{path}")

    def verify_clicked(self):
        name = self.name_input.text().strip()
        if not name or not self.photo_path:
            QMessageBox.warning(self, "Missing Info", "Please enter your name and upload a reference photo.")
            return
        self.verify_and_continue(name, self.photo_path)  # ✅ Hooked for actual backend verification

class TwoFAPage(QWidget):
    def __init__(self, navigate_back):
        super().__init__()
        self.verification_code = None
        self.navigate_back = navigate_back
        layout = QVBoxLayout()
        layout.setSpacing(20)

        layout.addWidget(self.title_label("Two-Factor Authentication (2FA)"))
        layout.addWidget(self.sub_label("Enter your email address to receive a verification code:"))

        self.email_input = self.create_input("Enter your email")
        self.code_input = self.create_input("Enter verification code")

        send_button = self.create_button("Send Verification Code", self.send_code)
        verify_button = self.create_button("Verify Code", self.verify_code)
        back_button = self.create_button("Back", navigate_back, text_link=True)

        layout.addWidget(self.email_input)
        layout.addWidget(send_button)
        layout.addWidget(self.code_input)
        layout.addWidget(verify_button)
        layout.addWidget(back_button)
        layout.addStretch()
        self.setLayout(layout)

    def title_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        label.setStyleSheet("color: #003366;")
        label.setAlignment(Qt.AlignCenter)
        return label

    def sub_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 12))
        label.setAlignment(Qt.AlignCenter)
        return label

    def create_input(self, placeholder):
        box = QLineEdit()
        box.setPlaceholderText(placeholder)
        box.setMinimumHeight(35)
        box.setStyleSheet("""
            QLineEdit {
                border-radius: 15px;
                border: 2px solid #ccc;
                padding-left: 15px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2.5px solid #1a73e8;
            }
        """)
        return box

    def create_button(self, text, handler, text_link=False):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(35)
        if text_link:
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #003366;
                    border: none;
                    font-size: 12px;
                    text-decoration: underline;
                }
                QPushButton:hover {
                    color: #1a73e8;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #004aad;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
        button.clicked.connect(handler)
        return button

    def send_code(self):
        email = self.email_input.text().strip()
        if not email or "@" not in email:
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        self.verification_code = generate_otp()
        send_otp_email(email, self.verification_code)
        QMessageBox.information(self, "Code Sent", f"A verification code was sent to {email}.")

    def verify_code(self):
        if self.code_input.text().strip() == self.verification_code:
            QMessageBox.information(self, "Verified", "Email verified successfully.")
            self.navigate_back()
        else:
            QMessageBox.warning(self, "Error", "Incorrect verification code.")



class ProjectDetailsPage(QWidget):
    def __init__(self, navigate_back):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        layout.addWidget(self.label("Project Details", big=True))
        layout.addWidget(self.description())
        layout.addStretch()
        layout.addWidget(self.button("Back", navigate_back))
        self.setLayout(layout)

    def label(self, text, big=False):
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 20 if big else 14, QFont.Bold if big else QFont.Normal))
        label.setStyleSheet("color: #003366;" if big else "color: #333333;")
        label.setAlignment(Qt.AlignCenter if big else Qt.AlignTop)
        return label

    def description(self):
        desc = QLabel(
            "Kansel AI Proctoring System\n\n"
            "Created by Khogula Kannan.\n\n"
            "It includes live candidate verification, voice activity detection,\n"
            "gaze tracking, browser logging, and automated reports.\n\n"
            "User-friendly interface and secure 2FA support."
        )
        desc.setWordWrap(True)
        desc.setFont(QFont("Segoe UI", 14))
        desc.setStyleSheet("color: #333333;")
        return desc

    def button(self, text, handler):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(35)
        button.setStyleSheet("""
            QPushButton {
                background-color: #004aad;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding-left: 20px;
                padding-right: 20px;
            }
        """)
        button.clicked.connect(handler)
        return button


class KanselMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kansel AI Proctoring")
        self.setMinimumSize(950, 500)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #c2d9ff, stop:1 #f0f5ff);
                font-family: 'Segoe UI';
            }
        """)

        self.pages = QStackedLayout()

        self.home_page = HomePage(
            navigate_to_candidate=self.show_candidate_page,
            navigate_to_project=self.show_project_details_page
        )
        self.candidate_page = CandidatePage(self.verify_and_continue, self.show_home_page)
        self.two_fa_page = TwoFAPage(self.show_exam_page)
        self.project_details_page = ProjectDetailsPage(self.show_home_page)

        self.exam_page = QWidget()
        exam_layout = QVBoxLayout()
        exam_layout.addWidget(QLabel("Exam In Progress", alignment=Qt.AlignCenter))
        self.end_exam_button = QPushButton("End Exam")  # ✅ Single reference
        self.end_exam_button.setStyleSheet("background-color:#d32f2f; color:white; font-weight:bold; padding:8px;")
        exam_layout.addWidget(self.end_exam_button, alignment=Qt.AlignCenter)
        self.exam_page.setLayout(exam_layout)


        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.candidate_page)
        self.pages.addWidget(self.two_fa_page)
        self.pages.addWidget(self.project_details_page)
        self.pages.addWidget(self.exam_page)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        main_layout.addWidget(LogoWidget())
        main_layout.addLayout(self.pages)

        self.setLayout(main_layout)
        self.show_home_page()

    def show_home_page(self): self.pages.setCurrentIndex(0)
    def show_candidate_page(self): self.pages.setCurrentIndex(1)
    def show_2fa_page(self): self.pages.setCurrentIndex(2)
    def show_project_details_page(self): self.pages.setCurrentIndex(3)
    def show_exam_page(self): self.pages.setCurrentIndex(4)

    def verify_and_continue(self, name, photo_path):
        self.show_2fa_page()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KanselMainWindow()
    window.show()
    sys.exit(app.exec_())
