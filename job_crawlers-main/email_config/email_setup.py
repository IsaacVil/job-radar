import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Gmail account the alerts are sent from. JOB_RADAR_EMAIL_PASSWORD must be a Google app password,
# not the account password. JOB_RADAR_DEFAULT_RECEIVER is used when no email comes from the frontend.
FROM_EMAIL = os.environ.get("JOB_RADAR_EMAIL", "")
FROM_PASSWORD = os.environ.get("JOB_RADAR_EMAIL_PASSWORD", "")
DEFAULT_RECEIVER = os.environ.get("JOB_RADAR_DEFAULT_RECEIVER", "")


def send_email(job_details_list, receiverEmail=None):
    to_email = receiverEmail or DEFAULT_RECEIVER

    if not to_email:
        return  # Email is an optional extra channel: the push notification is the default one
    if not FROM_EMAIL or not FROM_PASSWORD:
        print("No sender credentials, skipping the notification. Set JOB_RADAR_EMAIL and JOB_RADAR_EMAIL_PASSWORD.")
        return

    subject = "New " + job_details_list[0]['company'] + " Job Posting: "

    # Concatenate job details for all jobs into a single string
    body = ""
    for job_details in job_details_list:
        body += f"Job Title: {job_details['title']}\n"
        body += f"Job Number: {job_details['number']}\n"
        if job_details.get('location'):
            body += f"Location: {job_details['location']}\n"
        body += f"Job Link: {job_details['link']}\n\n"

    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(FROM_EMAIL, FROM_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"Email sent successfully to {to_email}.")
    except smtplib.SMTPAuthenticationError:
        print("Failed to authenticate with the email server. Check JOB_RADAR_EMAIL / JOB_RADAR_EMAIL_PASSWORD.")
    except smtplib.SMTPException as error:
        print(f"SMTP error occurred: {error}")
