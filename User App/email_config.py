"""
Configuración y Utilidades de Email para Sistema de Reservas de Cancha de Tenis
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
from admin_database import admin_db_manager

# Configuración de email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

class EmailManager:
    """Administrador de envío de emails para el sistema de reservas"""

    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT

        try:
            self.email_address = st.secrets["email"]["address"]
            self.email_password = st.secrets["email"]["password"]
        except KeyError:
            st.warning("⚠️ Credenciales de email no configuradas...")

    def generate_verification_code(self) -> str:
        """Generar código de verificación de 6 caracteres"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    def is_configured(self) -> bool:
        """Verificar si el email está configurado correctamente"""
        try:
            return bool(st.secrets["email"]["address"] and st.secrets["email"]["password"])
        except KeyError:
            return False

    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = None) -> Tuple[bool, str]:
        """Enviar email con HTML y texto alternativo opcional"""
        if not self.is_configured():
            return False, "Servicio de email no configurado"

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

            return True, "Email enviado exitosamente"

        except Exception as e:
            return False, f"Error al enviar email: {str(e)}"

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
        event_start = date.replace(hour=sorted_hours[0], minute=0, second=0)
        event_end = date.replace(hour=sorted_hours[-1] + 1, minute=0, second=0)

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

        # Al inicio del método, después de obtener la información básica:
        lock_code = admin_db_manager.get_current_lock_code() or "Contactar admin"


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
                        <div style="
    background: linear-gradient(135deg, #FFD400 0%, #FFC107 100%);
    border: 3px solid #FF6F00;
    border-radius: 15px;
    padding: 25px;
    margin: 25px 0;
    text-align: center;
    box-shadow: 0 8px 16px rgba(255, 111, 0, 0.3);
">
    <h2 style="
        margin: 0 0 15px 0; 
        color: #B71C1C; 
        font-size: 1.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    ">
        🔒 CÓDIGO DEL CANDADO
    </h2>
    <div style="
        font-size: 3.5rem;
        font-weight: bold;
        color: #B71C1C;
        margin: 20px 0;
        font-family: 'Courier New', monospace;
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: inset 0 4px 8px rgba(0,0,0,0.2);
        border: 2px solid #D32F2F;
        letter-spacing: 8px;
    ">
        {lock_code}
    </div>
    <p style="
        margin: 0; 
        color: #B71C1C; 
        font-weight: bold;
        font-size: 1.1rem;
    ">
        ¡Anota este código para abrir el candado!
    </p>
</div>
                        
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
        - 🔒🔒🔒 CÓDIGO DEL CANDADO: {lock_code} 🔒🔒🔒

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