import requests
import logging
import smtplib

from config.config import settings

from email.mime.text import MIMEText
from fastapi import status, HTTPException

logger = logging.getLogger("EmailVerifier")


class EmailVerifier:
    def __init__(self):
        self.mailboxlayer_key = settings.mailbox_api_key
        self.timeout = 10

    async def verify_email(self, email: str) -> bool:
        """Verify an email address using MailboxLayer API."""
        if not self.mailboxlayer_key:
            logger.warning('MailboxLayer API key not configured, skipping verification')
            return False

        try:
            url = (
                f"https://apilayer.net/api/check?"
                f"access_key={self.mailboxlayer_key}&"
                f"email={email}&"
                "smtp=1&format=1"
            )

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            logger.debug('MailboxLayer response: %s', data)

            # Validate response structure
            if not isinstance(data, dict):
                logger.error('Unexpected API response format')
                return False
            
            # Check critical email validity flags
            is_valid = (
                data.get('format_valid', False) and
                data.get('mx_found', False) and
                not data.get('disposable', False)
            )

            if not is_valid and 'did_you_mean' in data:
                logger.info("Suggested email correction: %s", data['did_you_mean'])

            return is_valid

        except requests.exceptions.RequestException as e:
            logger.error("MailboxLayer API request failed: %s", str(e))
            return False
        except Exception as e:
            logger.error('Email verification failed: %s', str(e))
            return False
            
class EmailSender:
     def __init__(self):
          self.smtp_host = settings.locale_smtp_host
          self.smtp_port = settings.locale_smtp_port
          self.smtp_user = settings.locale_email_address
          self.smtp_password = settings.locale_email_password

     async def send_verification_email(self, email: str, token: str):
          try:
               verify_url = f"{settings.locale_frontend_url}/verify-email?token={token}"
            
               # Build email message
               message = MIMEText(
                    f"Please verify your email by clicking: {verify_url}\n\n"
                    f"If you didn't request this, please ignore this email."
                    )
               message['Subject'] = 'Verify your email'
               message['From'] = self.smtp_user
               message['To'] = email

               with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)
               logger.info(f'verification email sent to {email}')
          except Exception as e:
               logger.error(f'failed to send verification email: {str(e)}')
               raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail= 'Email service temporarily unavailable'
               )
               
