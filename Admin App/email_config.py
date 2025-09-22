"""
Configuración y Utilidades de Email para Sistema de Reservas de Cancha de Tenis
"""

import pytz
import smtplib
import ssl
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Tuple
import streamlit as st

# Configuración de email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

class EmailManager:
    """Administrador de envío de emails para el sistema de reservas"""

    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self._configured = False
        self.email_address = None
        self.email_password = None

        # Safely load email credentials
        self._load_email_credentials()

    def _load_email_credentials(self):
        """Safely load email credentials from secrets"""
        try:
            self.email_address = st.secrets["email"]["address"]
            self.email_password = st.secrets["email"]["password"]

            # Validate credentials format
            if not self.email_address or not self.email_password:
                self._configured = False
                return

            # Basic email format validation
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email_address):
                self._configured = False
                st.error("❌ Invalid email address format in secrets")
                return

            # Validate app password format (Gmail app passwords are typically 16 chars)
            if len(self.email_password) < 10:
                self._configured = False
                st.error("❌ Email password appears to be invalid (too short)")
                return

            self._configured = True

            # Log success without exposing credentials
            print(f"✅ Email configured for: {self.email_address[:3]}***@{self.email_address.split('@')[1]}")

        except KeyError as e:
            self._configured = False
            # Don't log the specific missing key to avoid information leakage
            print("⚠️ Email credentials not configured in secrets")
        except Exception as e:
            self._configured = False
            # Log error without exposing sensitive information
            print(f"❌ Error loading email configuration: {type(e).__name__}")
            st.error("❌ Error loading email configuration")

    def generate_verification_code(self) -> str:
        """Generar código de verificación de 6 caracteres"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    def is_configured(self) -> bool:
        """Verificar si el email está configurado correctamente"""
        return self._configured

    def get_configuration_status(self) -> dict:
        """Get detailed configuration status for admin debugging"""
        if not self._configured:
            try:
                # Check what's missing without exposing values
                address_exists = "address" in st.secrets.get("email", {})
                password_exists = "password" in st.secrets.get("email", {})

                return {
                    "configured": False,
                    "address_present": address_exists,
                    "password_present": password_exists,
                    "smtp_server": self.smtp_server,
                    "smtp_port": self.smtp_port
                }
            except Exception:
                return {"configured": False, "error": "Cannot access secrets"}
        else:
            return {
                "configured": True,
                "email": f"{self.email_address[:3]}***@{self.email_address.split('@')[1]}",
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port
            }

    def validate_email_security(self) -> bool:
        """Validate email configuration security"""
        if not self._configured:
            st.warning("⚠️ Email service not configured")
            return False

        # Check for common security issues
        warnings = []

        # Check if using a secure app password (not regular password)
        if " " not in self.email_password:
            warnings.append("Consider using an App Password instead of regular password")

        # Check email provider security
        email_domain = self.email_address.split('@')[1].lower()
        if email_domain not in ['gmail.com', 'outlook.com', 'hotmail.com']:
            warnings.append(f"Using {email_domain} - ensure 2FA is enabled")

        # Display warnings to admin
        if warnings:
            for warning in warnings:
                st.info(f"💡 Email Security: {warning}")

        return True

    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = None) -> Tuple[bool, str]:
        """Enviar email con HTML y texto alternativo opcional"""
        if not self.is_configured():
            return False, "Email service not configured"

        # Validate recipient email
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', to_email):
            return False, "Invalid recipient email format"

        try:
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_address
            message["To"] = to_email

            # Agregar versión de texto si se proporciona
            if body_text:
                text_part = MIMEText(body_text, "plain")
                message.attach(text_part)

            # Agregar versión HTML
            html_part = MIMEText(body_html, "html")
            message.attach(html_part)

            # Crear conexión segura y enviar
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, message.as_string())

            # Log success without exposing email addresses
            recipient_masked = f"{to_email[:3]}***@{to_email.split('@')[1]}"
            print(f"✅ Email sent successfully to {recipient_masked}")

            return True, "Email sent successfully"

        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed - check email credentials"
            print(f"❌ {error_msg}")
            return False, error_msg
        except smtplib.SMTPRecipientsRefused:
            error_msg = "Recipient email address rejected"
            print(f"❌ {error_msg}")
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {type(e).__name__}"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Email sending failed: {type(e).__name__}"
            print(f"❌ {error_msg}")
            # Don't expose the full error message to avoid information leakage
            return False, "Email sending failed due to system error"

    def send_verification_email(self, to_email: str, verification_code: str, user_name: str) -> Tuple[bool, str]:
        """Enviar código de verificación por email"""
        subject = "🎾 Verifica tu Cuenta del Sistema de Reservas"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }}
                .code {{ background: #FFD400; color: #FFFFFF; font-size: 36px; font-weight: bold; padding: 20px; text-align: center; border-radius: 8px; letter-spacing: 8px; }}
                .footer {{ text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎾 Reservas de Cancha de Tenis</h1>
                    <p>¡Bienvenido a la cancha pública de Colina Campestre!</p>
                </div>

                <div class="content">
                    <h2>¡Hola {user_name}!</h2>
                    <p>Gracias por crear tu cuenta para reservar la cancha ubicada en la 148 con 56a. Para completar tu registro, por favor usa este código de verificación:</p>

                    <div class="code">{verification_code}</div>

                    <p>Este código expirará en 10 minutos por razones de seguridad.</p>

                    <p>Si no creaste esta cuenta, por favor ignora este email.</p>
                </div>

                <div class="footer">
                    <p>Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
                    <p>Este es un mensaje automatizado, por favor no respondas a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Sistema de Reservas de Cancha de Tenis - Verificación de Email

        ¡Hola {user_name}!

        Gracias por crear tu cuenta. Por favor usa este código de verificación para completar tu registro:

        {verification_code}

        Este código expira en 10 minutos.

        Si no creaste esta cuenta, por favor ignora este email.

        Sistema de Reservas de Cancha de Tenis - Colina Campestre
        """

        return self.send_email(to_email, subject, html_body, text_body)

    def send_reservation_confirmation(self, to_email: str, user_name: str, date: datetime, hours: list,
                                      reservation_details: dict) -> Tuple[bool, str]:
        """Enviar email de confirmación de reserva con evento de calendario"""
        subject = f"🎾 Reserva Confirmada - {date.strftime('%d de %B, %Y')}"

        # Formatear horas
        sorted_hours = sorted(hours)
        start_time = f"{sorted_hours[0]:02d}:00"
        end_time = f"{(sorted_hours[-1] + 1):02d}:00"

        # Crear datos del evento de calendario
        colombia_tz = pytz.timezone('America/Bogota')
        event_start = colombia_tz.localize(date.replace(hour=sorted_hours[0], minute=0, second=0))
        event_end = colombia_tz.localize(date.replace(hour=sorted_hours[-1] + 1, minute=0, second=0))

        # Formatear fechas para calendario (formato UTC)
        cal_start = event_start.strftime('%Y%m%dT%H%M%S')
        cal_end = event_end.strftime('%Y%m%dT%H%M%S')

        # Nombres de meses en español
        months_es = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                     'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        days_es = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']

        day_name = days_es[date.weekday()]
        month_name = months_es[date.month - 1]
        formatted_date = f"{day_name}, {date.day} de {month_name} de {date.year}"

        # Enlace de Google Calendar
        calendar_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text=Reserva%20Cancha%20de%20Tenis&dates={cal_start}/{cal_end}&details=Reserva%20de%20Cancha%20de%20Tenis%20en%20Colina%20Campestre%0A%0AReservado%20por:%20{user_name}%0AEmail:%20{to_email}&location=Cancha%20de%20Tenis%20Colina%20Campestre"

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
                    <h1>🎾 ¡Reserva Confirmada!</h1>
                </div>

                <div class="content">
                    <h2>¡Hola {user_name}!</h2>
                    <p>¡Excelentes noticias! Tu reserva ha sido confirmada. Aquí están los detalles:</p>

                    <div class="reservation-details">
                        <h3>📅 Detalles de la Reserva</h3>
                        <p><strong>Nombre:</strong> {user_name}</p>
                        <p><strong>Fecha:</strong> {formatted_date}</p>
                        <p><strong>Hora:</strong> {start_time} - {end_time}</p>
                        <p><strong>Duración:</strong> {len(hours)} hora(s)</p>
                        <p><strong>Ubicación:</strong> Cancha de Tenis Colina Campestre</p>
                    </div>

                    <p style="text-align: center;">
                        <a href="{calendar_link}" class="calendar-button" target="_blank">
                            📅 Agregar a Google Calendar
                        </a>
                    </p>

                    <p><small>¿Problemas con el botón? Copia este enlace: {calendar_link}</small></p>
                </div>

                <div class="footer">
                    <p>Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
                    <p>Esta es una confirmación automatizada. Por favor no respondas a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Nombres de meses en español
        months_es = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                     'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        days_es = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']

        day_name = days_es[date.weekday()]
        month_name = months_es[date.month - 1]
        formatted_date = f"{day_name}, {date.day} de {month_name} de {date.year}"

        text_body = f"""
        ¡Reserva de Cancha de Tenis Confirmada!

        ¡Hola {user_name}!

        Tu reserva de cancha de tenis ha sido confirmada:

        Detalles de la Reserva:
        - Nombre: {user_name}
        - Fecha: {formatted_date}
        - Hora: {start_time} - {end_time}
        - Duración: {len(hours)} hora(s)
        - Ubicación: Cancha de Tenis Colina Campestre

        Agregar a Google Calendar: {calendar_link}

        Sistema de Reservas de Cancha de Tenis - Colina Campestre
        """

        return self.send_email(to_email, subject, html_body, text_body)

    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> Tuple[bool, str]:
        """Enviar email de recuperación de contraseña"""
        subject = "🔒 Recuperación de Contraseña - Sistema de Reservas"

        # Crear enlace de recuperación (ajusta la URL según tu despliegue)
        reset_link = f"https://reservas-tenis-colina.streamlit.app/?reset_token={reset_token}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }}
                .reset-button {{ background: #DC143C; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }}
                .warning {{ background: #FFF3CD; border: 1px solid #FFEAA7; padding: 15px; border-radius: 5px; color: #856404; }}
                .footer {{ text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Recuperación de Contraseña</h1>
                    <p>Sistema de Reservas de Cancha de Tenis</p>
                </div>

                <div class="content">
                    <h2>Hola {user_name},</h2>
                    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>

                    <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>

                    <p style="text-align: center;">
                        <a href="{reset_link}" class="reset-button">
                            🔒 Restablecer Contraseña
                        </a>
                    </p>

                    <div class="warning">
                        <strong>⚠️ Importante:</strong>
                        <ul>
                            <li>Este enlace expira en 30 minutos</li>
                            <li>Solo se puede usar una vez</li>
                            <li>Si no solicitaste este cambio, ignora este email</li>
                        </ul>
                    </div>

                    <p><small>Si tienes problemas con el botón, copia este enlace: {reset_link}</small></p>
                </div>

                <div class="footer">
                    <p>Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
                    <p>Este es un mensaje automatizado, por favor no respondas.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Recuperación de Contraseña - Sistema de Reservas

        Hola {user_name},

        Recibimos una solicitud para restablecer tu contraseña.

        Usa este enlace para crear una nueva contraseña:
        {reset_link}

        IMPORTANTE:
        - Este enlace expira en 30 minutos
        - Solo se puede usar una vez
        - Si no solicitaste este cambio, ignora este email

        Sistema de Reservas de Cancha de Tenis - Colina Campestre
        """

        return self.send_email(to_email, subject, html_body, text_body)

# Instancia global
email_manager = EmailManager()