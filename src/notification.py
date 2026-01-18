import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging
import os
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/transformation_and_notifications.log', mode = 'w'),
        logging.StreamHandler()
    ],
    force=True
)

def smtp_send_email(sender_email, sender_password, recipient_email, subject, body, folder_path, keyword=None): 
    
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  
    
    try:
        message = MIMEMultipart()
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = recipient_email
        message.attach(MIMEText(body, "plain"))

        if folder_path and os.path.exists(folder_path):
            csv_files = [
                f for f in os.listdir(folder_path) if f.endswith(".csv") and (keyword.lower() in f.lower() if keyword else True)
            ]

            if not csv_files:
                logging.warning(f"No CSV file found in {folder_path}")

            else:
                logging.info(f"found {len(csv_files)} in {folder_path}")
                for file_name in csv_files:
                    file_path = os.path.join(folder_path, file_name)
                    with open(file_path, 'rb') as file:
                        part = MIMEApplication(file.read(), Name = file_name)
                        message.attach(part)
                        logging.info(f"Attached {file_name}!")

        logging.info("Sending email...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()          # Identify ourselves to the server
            server.starttls()      # Upgrade connection to encrypted TLS
            server.ehlo()          # Re-identify after encryption
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
            logging.info(f"Email sent successfully to {recipient_email}")

        return True
    
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        raise

def discord_webhook(discord_webhook_url,content, username):
    try:
        payload = {
            "content": content,
            "username":username
        }
        result = requests.post(discord_webhook_url, json=payload)
        result.raise_for_status()
        logging.info(f"Sucessfully send to discord channel! - status code {result.status_code}")

    except Exception as e:
        logging.error(f"Error sending to discord channel! - status code {result.status_code}")
        raise


    
