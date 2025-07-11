import smtplib
import random
from email.message import EmailMessage

EXAMINER_EMAIL = ""  # Default examiner email here
SENDER_EMAIL = ''  # Your sender email
SENDER_PASSWORD = ''  # Your sender email password

# === Existing Function: Email alert for malpractice ===
def send_malpractice_email(candidate_name, report_path, malpractice_details, attachments=[]):
    msg = EmailMessage()

    # Detect if there was no malpractice
    no_malpractice = (not malpractice_details) or (malpractice_details.strip().lower() in ["no major violations.", "no malpractice"])

    if no_malpractice:
        msg['Subject'] = f"Exam Completed Successfully - {candidate_name}"
        body = f"""\
Dear Examiner,

The exam for candidate {candidate_name} was completed successfully.

✅ No malpractice was detected during the session.

Please find attached the proctoring report for your reference.

Regards,
AI Proctoring System
"""
    else:
        msg['Subject'] = f"Malpractice Alert for Candidate: {candidate_name}"
        body = f"""\
Dear Examiner,

Malpractice was detected during the proctoring session of candidate: {candidate_name}.

Details:
{malpractice_details}

Please find attached the proctoring report and evidence snapshots.

Regards,
AI Proctoring System
"""

    msg['From'] = SENDER_EMAIL
    msg['To'] = EXAMINER_EMAIL
    msg.set_content(body)

    # Attach report PDF
    with open(report_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=report_path)

    # Attach evidence images if any
    if not no_malpractice:
        for filepath in attachments:
            with open(filepath, 'rb') as f:
                file_data = f.read()
                file_name = filepath.split("/")[-1]
                msg.add_attachment(file_data, maintype='image', subtype='jpeg', filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

# === New Function: 2FA OTP email ===
def send_otp_email(to_email, otp_code):
    msg = EmailMessage()
    msg['Subject'] = "Your OTP Code for Exam Login"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    msg.set_content(f"""\
Dear Candidate,

Your One-Time Password (OTP) for starting the exam is:

🔐 OTP: {otp_code}

Please enter this code in the system to verify your identity.

Note: This code is valid for one login attempt only.

Regards,
AI Proctoring System
""")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

# === New Function: Generate 6-digit OTP ===
def generate_otp():
    return str(random.randint(100000, 999999))
