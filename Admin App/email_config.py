"""
Configuración y Utilidades de Email para Sistema de Reservas de Cancha de Tenis
"""

import pytz
import smtplib
import ssl
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

    def is_configured(self) -> bool:
        """Verificar si el email está configurado correctamente"""
        return self._configured

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

        # Nombres de meses y días en español
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

    def send_account_blocked_notification(self, user_email: str, user_name: str) -> bool:
        """Send notification when a user account is blocked"""
        subject = "⚠️ Tu cuenta ha sido bloqueada - Sistema de Reservas"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
                .warning-box {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">⚠️ Cuenta Bloqueada</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Sistema de Reservas - Cancha de Tenis</p>
                </div>

                <div class="content">
                    <p>Hola <strong>{user_name}</strong>,</p>

                    <div class="warning-box">
                        <p style="margin: 0;"><strong>Tu cuenta ha sido bloqueada.</strong></p>
                    </div>

                    <p>No podrás acceder al sistema de reservas hasta que tu cuenta sea reactivada.</p>

                    <p><strong>¿Qué hacer ahora?</strong></p>
                    <p>Por favor contacta al administrador de la aplicación para más información sobre el bloqueo de tu cuenta.</p>

                    <p style="margin-top: 30px;">Gracias por tu comprensión.</p>
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
        Cuenta Bloqueada - Sistema de Reservas

        Hola {user_name},

        Tu cuenta ha sido bloqueada.

        No podrás acceder al sistema de reservas hasta que tu cuenta sea reactivada.

        Por favor contacta al administrador de la aplicación para más información.

        Sistema de Reservas de Cancha de Tenis - Colina Campestre
        """

        return self.send_email(user_email, subject, html_body, text_body)

    def send_account_reactivated_notification(self, user_email: str, user_name: str) -> bool:
        """Send notification when a user account is reactivated"""
        subject = "✅ Tu cuenta ha sido reactivada - Sistema de Reservas"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%);
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #ddd; }}
                .success-box {{ background: #d4edda; border-left: 4px solid #28a745;
                                padding: 15px; margin: 20px 0; border-radius: 4px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center;
                          border-radius: 0 0 10px 10px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">🎾 Sistema de Reservas</h1>
                    <p style="margin: 10px 0 0 0;">Notificación de Cuenta</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{user_name}</strong>,</p>
                    <div class="success-box">
                        <p style="margin: 0;"><strong>✅ Tu cuenta ha sido reactivada.</strong></p>
                    </div>
                    <p>Ya puedes acceder nuevamente al sistema de reservas y realizar tus reservas de cancha de tenis.</p>
                    <p>Si tienes alguna pregunta, no dudes en contactar al administrador.</p>
                    <p>¡Bienvenido de vuelta!</p>
                </div>
                <div class="footer">
                    <p style="margin: 0;">Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Hola {user_name},

        ✅ Tu cuenta ha sido reactivada.

        Ya puedes acceder nuevamente al sistema de reservas y realizar tus reservas de cancha de tenis.

        Si tienes alguna pregunta, no dudes en contactar al administrador.

        ¡Bienvenido de vuelta!

        Sistema de Reservas de Cancha de Tenis - Colina Campestre
        """

        return self.send_email(user_email, subject, html_body, text_body)

    def send_reservation_cancelled_notification(self, user_email: str, user_name: str, date: str, hour: int, cancelled_by: str = "user", reason: str = "") -> bool:
        """
        Send notification when a reservation is cancelled

        Args:
            user_email: User's email address
            user_name: User's full name
            date: Reservation date (YYYY-MM-DD)
            hour: Reservation hour (0-23)
            cancelled_by: Who cancelled ('user' or 'admin')
            reason: Cancellation reason (optional)
        """
        from timezone_utils import format_date_display

        subject = "🚫 Reserva Cancelada - Sistema de Reservas"
        formatted_date = format_date_display(date)
        hour_display = f"{hour:02d}:00"

        cancellation_reason = "Has cancelado tu reserva" if cancelled_by == "user" else "Tu reserva ha sido cancelada por el administrador"

        # Build reason section
        if reason and reason.strip():
            reason_html = f"""
            <div class="info-box" style="background: #fff3cd; border-left: 4px solid #ffc107;">
                <p style="margin: 5px 0;"><strong>📋 Motivo de la cancelación:</strong></p>
                <p style="margin: 5px 0;">{reason}</p>
            </div>
            """
            reason_text = f"\n📋 Motivo de la cancelación: {reason}\n"
        else:
            reason_html = """
            <div class="info-box" style="background: #e3f2fd; border-left: 4px solid #2478CC;">
                <p style="margin: 5px 0;">Para más información sobre la cancelación, por favor contacta al administrador del sistema.</p>
            </div>
            """
            reason_text = "\nPara más información sobre la cancelación, por favor contacta al administrador del sistema.\n"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%);
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #ddd; }}
                .cancel-box {{ background: #fff3cd; border-left: 4px solid #ffc107;
                               padding: 15px; margin: 20px 0; border-radius: 4px; }}
                .info-box {{ background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center;
                          border-radius: 0 0 10px 10px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">🎾 Sistema de Reservas</h1>
                    <p style="margin: 10px 0 0 0;">Confirmación de Cancelación</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{user_name}</strong>,</p>
                    <div class="cancel-box">
                        <p style="margin: 0;"><strong>🚫 {cancellation_reason}</strong></p>
                    </div>
                    <div class="info-box">
                        <p style="margin: 5px 0;"><strong>📅 Fecha:</strong> {formatted_date}</p>
                        <p style="margin: 5px 0;"><strong>🕐 Hora:</strong> {hour_display}</p>
                    </div>
                    {reason_html}
                    <p>La cancelación se ha procesado exitosamente. El crédito utilizado para esta reserva ha sido devuelto a tu cuenta.</p>
                    <p>Puedes hacer una nueva reserva cuando lo desees ingresando a la aplicación.</p>
                    <p>¡Gracias por usar nuestro sistema!</p>
                </div>
                <div class="footer">
                    <p style="margin: 0;">Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Hola {user_name},

        🚫 {cancellation_reason}

        Detalles de la reserva cancelada:
        📅 Fecha: {formatted_date}
        🕐 Hora: {hour_display}
        {reason_text}
        La cancelación se ha procesado exitosamente. El crédito utilizado para esta reserva ha sido devuelto a tu cuenta.

        Puedes hacer una nueva reserva cuando lo desees ingresando a la aplicación.

        ¡Gracias por usar nuestro sistema!

        Sistema de Reservas de Cancha de Tenis - Colina Campestre
        """

        return self.send_email(user_email, subject, html_body, text_body)

    def send_credits_notification(self, user_email: str, credits_amount: int, reason: str, operation: str) -> bool:
        """
        Send notification when user credits are modified

        Args:
            user_email: User's email address
            credits_amount: Number of credits added or removed
            reason: Reason for credit change
            operation: 'agregar' or 'remover'
        """
        try:
            if not self.is_configured():
                return False

            action = "agregados" if operation == "agregar" else "removidos"
            subject = f"🎾 Créditos {action.title()} - Sistema de Reservas"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%);
                              color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #ffffff; padding: 30px; border: 1px solid #ddd; }}
                    .credits-box {{ background: #f0f8ff; border-left: 4px solid #2478CC;
                                    padding: 15px; margin: 20px 0; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center;
                              border-radius: 0 0 10px 10px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">🎾 Sistema de Reservas</h1>
                        <p style="margin: 10px 0 0 0;">Actualización de Créditos</p>
                    </div>
                    <div class="content">
                        <p>Hola,</p>
                        <div class="credits-box">
                            <p style="margin: 0;"><strong>Se han {action} {credits_amount} crédito(s)</strong> {'a' if operation == 'agregar' else 'de'} tu cuenta.</p>
                        </div>
                        <p><strong>Motivo:</strong> {reason}</p>
                        <p>Puedes revisar tu saldo actual iniciando sesión en la aplicación.</p>
                        <p>¡Gracias por usar nuestro sistema de reservas!</p>
                    </div>
                    <div class="footer">
                        <p style="margin: 0;">Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            Actualización de Créditos

            Se han {action} {credits_amount} crédito(s) {'a' if operation == 'agregar' else 'de'} tu cuenta.

            Motivo: {reason}

            Revisa tu saldo actual en la aplicación.

            Sistema de Reservas de Cancha de Tenis - Colina Campestre
            """

            return self.send_email(user_email, subject, html_body, text_body)
        except Exception as e:
            print(f"Error sending credits notification: {e}")
            return False

# Instancia global
email_manager = EmailManager()