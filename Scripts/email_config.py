"""
Email Configuration and Utilities for Tennis Court Reservation System
"""

import smtplib
import ssl
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Tuple
import streamlit as st

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = st.secrets["email"]["address"]
EMAIL_PASSWORD = st.secrets["email"]["password"]



class EmailManager:
    """Manage email sending for the tennis court reservation system"""

    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        try:
            self.email_address = st.secrets["email"]["address"]
            self.email_password = st.secrets["email"]["password"]
        except KeyError:
            st.warning("⚠️ Email credentials not configured. Email features may not work.")


    def generate_verification_code(self) -> str:
        """Generate a 6-character verification code"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        try:
            return bool(st.secrets["email"]["address"] and st.secrets["email"]["password"])
        except KeyError:
            return False

    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = None) -> Tuple[bool, str]:
        """Send an email with HTML and optional text fallback"""
        if not self.is_configured():
            return False, "Email service not configured"

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_address
            message["To"] = to_email

            # Add text version if provided
            if body_text:
                text_part = MIMEText(body_text, "plain")
                message.attach(text_part)

            # Add HTML version
            html_part = MIMEText(body_html, "html")
            message.attach(html_part)

            # Create secure connection and send
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, message.as_string())

            return True, "Email sent successfully"

        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

    def send_verification_email(self, to_email: str, verification_code: str, user_name: str) -> Tuple[bool, str]:
        """Send email verification code"""
        subject = "🎾 Verify Your Tennis Court Account"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }}
                .code {{ background: #FFD400; color: #001854; font-size: 36px; font-weight: bold; padding: 20px; text-align: center; border-radius: 8px; letter-spacing: 8px; }}
                .footer {{ text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎾 Tennis Court Reservations</h1>
                    <p>Welcome to Colina Campestre!</p>
                </div>

                <div class="content">
                    <h2>Hi {user_name}!</h2>
                    <p>Thanks for creating your tennis court reservation account. To complete your registration, please use this verification code:</p>

                    <div class="code">{verification_code}</div>

                    <p>This code will expire in 10 minutes for security reasons.</p>

                    <p>If you didn't create this account, please ignore this email.</p>
                </div>

                <div class="footer">
                    <p>Tennis Court Reservation System - Colina Campestre</p>
                    <p>This is an automated message, please don't reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Tennis Court Reservations - Email Verification

        Hi {user_name}!

        Thanks for creating your account. Please use this verification code to complete your registration:

        {verification_code}

        This code expires in 10 minutes.

        If you didn't create this account, please ignore this email.

        Tennis Court Reservation System - Colina Campestre
        """

        return self.send_email(to_email, subject, html_body, text_body)

    def send_reservation_confirmation(self, to_email: str, user_name: str, date: datetime, hours: list,
                                      reservation_details: dict) -> Tuple[bool, str]:
        """Send reservation confirmation email with calendar event"""
        subject = f"🎾 Reservation Confirmed - {date.strftime('%B %d, %Y')}"

        # Format hours
        sorted_hours = sorted(hours)
        start_time = f"{sorted_hours[0]:02d}:00"
        end_time = f"{(sorted_hours[-1] + 1):02d}:00"

        # Create calendar event data
        event_start = date.replace(hour=sorted_hours[0], minute=0, second=0)
        event_end = date.replace(hour=sorted_hours[-1] + 1, minute=0, second=0)

        # Format dates for calendar (UTC format)
        cal_start = event_start.strftime('%Y%m%dT%H%M%S')
        cal_end = event_end.strftime('%Y%m%dT%H%M%S')

        # Google Calendar link
        calendar_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text=Tennis%20Court%20Reservation&dates={cal_start}/{cal_end}&details=Tennis%20Court%20Reservation%20at%20Colina%20Campestre%0A%0AReserved%20by:%20{user_name}%0AEmail:%20{to_email}&location=Colina%20Campestre%20Tennis%20Court"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }}
                .reservation-details {{ background: white; padding: 20px; border-radius: 8px; border-left: 5px solid #FFD400; }}
                .calendar-button {{ background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎾 Reservation Confirmed!</h1>
                    <p>Your court is ready!</p>
                </div>

                <div class="content">
                    <h2>Hi {user_name}!</h2>
                    <p>Great news! Your tennis court reservation has been confirmed. Here are the details:</p>

                    <div class="reservation-details">
                        <h3>📅 Reservation Details</h3>
                        <p><strong>Name:</strong> {user_name}</p>
                        <p><strong>Date:</strong> {date.strftime('%A, %B %d, %Y')}</p>
                        <p><strong>Time:</strong> {start_time} - {end_time}</p>
                        <p><strong>Duration:</strong> {len(hours)} hour(s)</p>
                        <p><strong>Location:</strong> Colina Campestre Tennis Court</p>
                    </div>

                    <p>Don't forget to bring your racket and be on time!</p>

                    <p style="text-align: center;">
                        <a href="{calendar_link}" class="calendar-button" target="_blank">
                            📅 Add to Google Calendar
                        </a>
                    </p>

                    <p><small>Having trouble with the button? Copy this link: {calendar_link}</small></p>
                </div>

                <div class="footer">
                    <p>Tennis Court Reservation System - Colina Campestre</p>
                    <p>This is an automated confirmation. Please don't reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Tennis Court Reservation Confirmed!

        Hi {user_name}!

        Your tennis court reservation has been confirmed:

        Reservation Details:
        - Name: {user_name}
        - Date: {date.strftime('%A, %B %d, %Y')}
        - Time: {start_time} - {end_time}
        - Duration: {len(hours)} hour(s)
        - Location: Colina Campestre Tennis Court

        Add to Google Calendar: {calendar_link}

        Tennis Court Reservation System - Colina Campestre
        """

        return self.send_email(to_email, subject, html_body, text_body)


# Global instance
email_manager = EmailManager()