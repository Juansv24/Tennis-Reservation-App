"""
Reservation Tab for Tennis Court Reservation System
UPDATED VERSION with Authentication Integration
"""

import streamlit as st
import datetime
from datetime import timedelta
from database_manager import db_manager
from auth_utils import get_current_user
from timezone_utils import get_colombia_today, get_colombia_now
from email_config import email_manager

# Configuración
COURT_HOURS = list(range(6, 22))  # 6 AM a 9 PM
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"

def get_today_tomorrow():
    """Obtener hoy y mañana"""
    today = get_colombia_today()
    tomorrow = today + timedelta(days=1)
    return today, tomorrow

def get_current_hour():
    """Obtener la hora actual"""
    return get_colombia_now().hour

def format_hour(hour: int) -> str:
    """Formatear hora para mostrar"""
    return f"{hour:02d}:00"

def format_date_short(date: datetime.date) -> str:
    """Formatear fecha corta"""
    days = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']
    months = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN',
              'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
    
    day_name = days[date.weekday()]
    month_name = months[date.month - 1]
    
    return f"{day_name} {date.day} {month_name}"

def format_date_full(date: datetime.date) -> str:
    """Formatear fecha completa"""
    days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    day_name = days[date.weekday()]
    month_name = months[date.month - 1]
    
    return f"{day_name}, {date.day} de {month_name} de {date.year}"

def apply_custom_css():
    """Aplicar CSS personalizado con colores US Open - ENHANCED VERSION"""
    st.markdown(f"""
    <style>
    .calendar-header {{
        background-color: {US_OPEN_LIGHT_BLUE};
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        font-weight: bold;
        font-size: 1.2rem;
    }}
                
    .time-slot-reserved {{
        background-color: #FFFFFF;
        border: 2px solid #E0E0E0;
        color: #C62828;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
        margin: 5px 0;
        cursor: not-allowed;
        opacity: 0.7;
    }}
    
    .time-slot-my-reservation {{
        background-color: #E8F5E8;
        border: 2px solid #4CAF50;
        color: #2E7D32;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
        margin: 5px 0;
        cursor: not-allowed;
        font-weight: bold;
    }}
    
    .time-slot-unavailable {{
        background-color: #F5F5F5;
        border: 2px solid #E0E0E0;
        color: #757575;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
        margin: 5px 0;
        cursor: not-allowed;
        opacity: 0.5;
    }}
    
    /* Enhanced success message */
    .success-message {{
        background: linear-gradient(135deg, #E8F5E8 0%, #F0FFF0 100%);
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 25px;
        margin: 20px 0;
        color: #2E7D32;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.2);
        animation: slide-in 0.5s ease-out;
    }}
    
    .stButton > button {{
        background-color: #FFFFFF;
        color: black;
        border: 2px solid {US_OPEN_LIGHT_BLUE};
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: white;
        color: {US_OPEN_BLUE};
        border-color: {US_OPEN_YELLOW};
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}

    /* User info display */
    .user-info-display {{
        background: linear-gradient(135deg, #F0F8FF 0%, #E6F3FF 100%);
        border: 2px solid {US_OPEN_LIGHT_BLUE};
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        color: {US_OPEN_BLUE};
    }}
    </style>
    """, unsafe_allow_html=True)

def show_reservation_tab():
    """Mostrar la pestaña de reservas"""
    apply_custom_css()
    
    # Obtener información del usuario actual
    current_user = get_current_user()
    if not current_user:
        st.error("Authentication error. Please refresh the page.")
        return
    
    today, tomorrow = get_today_tomorrow()
    current_hour = get_current_hour()
    
    # Obtener horas reservadas con nombres para cada día
    today_reservations = db_manager.get_reservations_with_names_for_date(today)
    tomorrow_reservations = db_manager.get_reservations_with_names_for_date(tomorrow)
    
    # Obtener reservas del usuario actual
    user_today_reservations = db_manager.get_user_reservations_for_date(current_user['email'], today)
    user_tomorrow_reservations = db_manager.get_user_reservations_for_date(current_user['email'], tomorrow)
    
    # Layout principal
    left_col, right_col = st.columns([1, 2])
    
    # Panel izquierdo - Detalles de reserva
    with left_col:
        show_reservation_details(today, tomorrow, current_user, user_today_reservations, user_tomorrow_reservations)
    
    # Panel derecho - Vista calendario
    with right_col:
        show_calendar_view(today, tomorrow, today_reservations, tomorrow_reservations, current_hour, current_user)

def show_reservation_details(today_date, tomorrow_date, current_user, user_today_reservations, user_tomorrow_reservations):
    """Mostrar panel de detalles de reserva"""
    st.subheader("Reservation Details")
    
    # Mostrar información del usuario
    st.markdown(f"""
    <div class="user-info-display">
        <strong>👤 Booking as:</strong><br>
        {current_user['full_name']}<br>
        <small>{current_user['email']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar reservas existentes del usuario
    show_user_existing_reservations(today_date, tomorrow_date, user_today_reservations, user_tomorrow_reservations)
    
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)
    
    # Mostrar reglas de reserva
    with st.expander("📋 Reservation Rules"):
        st.markdown("""
        • **Today and tomorrow bookings** allowed  
        • **Maximum 2 hours** per person per day  
        • **Consecutive hours** required if booking multiple slots  
        • **Court hours:** 6:00 AM - 9:00 PM  
        """)
    
    # Mostrar selección actual
    if selected_hours and selected_date is not None:
        st.markdown("### New Selection")
        
        st.write(f"**Date:** {format_date_full(selected_date)}")
        st.write(f"**Time Slots:** {len(selected_hours)} hour(s)")
        
        for hour in sorted(selected_hours):
            st.write(f"• {format_hour(hour)} - {format_hour(hour + 1)}")
        
        if len(selected_hours) > 1:
            start_time = format_hour(min(selected_hours))
            end_time = format_hour(max(selected_hours) + 1)
            st.write(f"**Total Time:** {start_time} - {end_time}")
        
        st.divider()
        
        # Formulario simplificado (sin nombre y email)
        st.markdown("### Confirm Reservation")
        
        # Mostrar resumen de la reserva
        st.info(f"Booking for: **{current_user['full_name']}** ({current_user['email']})")
        
        if st.button("✅ Confirm Reservation", type="primary", use_container_width=True):
            handle_reservation_submission(current_user, selected_date, selected_hours)
            
    else:
        st.info("Select time slots from the calendar to continue")
        
        st.markdown("### How to Reserve")
        st.write("1. **Select time slots** from today or tomorrow (up to 2 hours)")
        st.write("2. **Confirm your reservation** with one click")

def show_user_existing_reservations(today_date, tomorrow_date, user_today_reservations, user_tomorrow_reservations):
    """Mostrar reservas existentes del usuario"""
    has_reservations = bool(user_today_reservations or user_tomorrow_reservations)
    
    if has_reservations:
        st.markdown("### Your Current Reservations")
        
        if user_today_reservations:
            st.write(f"**Today ({format_date_short(today_date)}):** {len(user_today_reservations)} hour(s)")
            for hour in sorted(user_today_reservations):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")
        
        if user_tomorrow_reservations:
            st.write(f"**Tomorrow ({format_date_short(tomorrow_date)}):** {len(user_tomorrow_reservations)} hour(s)")
            for hour in sorted(user_tomorrow_reservations):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")
        
        st.divider()

def handle_reservation_submission(current_user, date, selected_hours):
    """Manejar el envío de la reserva - SIMPLIFICADO con autenticación"""
    
    # Validar límite de horas
    if len(selected_hours) > 2:
        st.error("Maximum 2 hours per day")
        return
    
    # Verificar que las horas sean consecutivas (si hay más de una)
    if len(selected_hours) > 1:
        sorted_hours = sorted(selected_hours)
        for i in range(1, len(sorted_hours)):
            if sorted_hours[i] - sorted_hours[i-1] != 1:
                st.error("Selected hours must be consecutive")
                return
    
    # Verificar límite por usuario (máximo 2 horas por día)
    user_existing_hours = db_manager.get_user_reservations_for_date(current_user['email'], date)
    if len(user_existing_hours) + len(selected_hours) > 2:
        st.error(f"You can only reserve 2 hours per day. You already have {len(user_existing_hours)} hour(s) reserved.")
        return

    # Intentar guardar todas las horas
    success_count = 0
    failed_hours = []

    for hour in selected_hours:
        if db_manager.save_reservation(date, hour, current_user['full_name'], current_user['email']):
            success_count += 1
        else:
            failed_hours.append(hour)

    # Mostrar resultado
    if success_count == len(selected_hours):
        # Éxito completo
        show_success_message(current_user['full_name'], date, selected_hours)

        # Send confirmation email
        send_reservation_confirmation_email(current_user, date, selected_hours)

        st.session_state.selected_hours = []
        st.session_state.selected_date = None
        st.balloons()
        
    elif success_count > 0:
        # Éxito parcial
        st.warning(f"Reserved {success_count} hour(s). The following were already taken: {', '.join(format_hour(h) for h in failed_hours)}")
        st.session_state.selected_hours = failed_hours  # Mantener las horas que fallaron para que el usuario pueda intentar otras
        
    else:
        # Falló completamente
        st.error("Unable to make reservation. All selected time slots are already taken.")

def send_reservation_confirmation_email(current_user, date, selected_hours):
    """Send reservation confirmation email"""
    try:
        # Check if email service is configured first
        if not email_manager.is_configured():
            st.info("📧 Email service not configured - reservation saved without email confirmation")
            return

        # Convert date to datetime for email
        date_datetime = datetime.datetime.combine(date, datetime.datetime.min.time())

        success, message = email_manager.send_reservation_confirmation(
            current_user['email'],
            current_user['full_name'],
            date_datetime,
            selected_hours,
            {}  # Additional reservation details if needed
        )

        if success:
            st.success("📧 Confirmation email sent!")
        else:
            st.warning(f"⚠️ Reservation saved but email failed: {message}")
            # Show the specific error for debugging
            with st.expander("Email Error Details"):
                st.write(message)

    except Exception as e:
        st.warning("⚠️ Reservation saved but email notification failed")
        # Show error details for debugging
        with st.expander("Error Details"):
            st.write(f"Error: {str(e)}")
        st.info("💡 Your reservation is confirmed even without the email")

def show_success_message(name, date_obj, selected_hours):
    """Mostrar mensaje de éxito"""
    sorted_hours = sorted(selected_hours)
    start_time = format_hour(min(sorted_hours))
    end_time = format_hour(max(sorted_hours) + 1)
    
    st.markdown(f"""
    <div class="success-message">
        <h3>✅ Reservation Confirmed!</h3>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Date:</strong> {format_date_full(date_obj)}</p>
        <p><strong>Time:</strong> {start_time} - {end_time}</p>
        <p><strong>Duration:</strong> {len(sorted_hours)} hour(s)</p>
    </div>
    """, unsafe_allow_html=True)

def show_calendar_view(today, tomorrow, today_reservations, tomorrow_reservations, current_hour, current_user):
    """Mostrar vista de calendario"""
    st.subheader("Court Availability")
    
    # Crear dos columnas para los dos días
    today_col, tomorrow_col = st.columns(2)
    
    # Columna de hoy
    with today_col:
        st.markdown(f"""
        <div class="calendar-header">
            {format_date_short(today)}<br>
            <small>TODAY</small>
        </div>
        """, unsafe_allow_html=True)
        
        show_day_schedule(today, today_reservations, current_user, is_today=True, current_hour=current_hour)
    
    # Columna de mañana
    with tomorrow_col:
        st.markdown(f"""
        <div class="calendar-header">
            {format_date_short(tomorrow)}<br>
            <small>TOMORROW</small>
        </div>
        """, unsafe_allow_html=True)
        
        show_day_schedule(tomorrow, tomorrow_reservations, current_user, is_today=False, current_hour=current_hour)

def show_day_schedule(date, reservations_dict, current_user, is_today=False, current_hour=None):
    """Mostrar horarios para un día específico - ENHANCED with user reservations"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)
    user_reservations = db_manager.get_user_reservations_for_date(current_user['email'], date)
    
    for hour in COURT_HOURS:
        is_reserved = hour in reservations_dict
        is_my_reservation = hour in user_reservations
        is_selected = hour in selected_hours and selected_date == date
        is_past_hour = is_today and current_hour is not None and hour < current_hour
        is_selectable = not is_reserved and not is_past_hour
        
        # Determinar el estado del botón
        if is_my_reservation:
            # Es una reserva del usuario actual
            button_text = f"{format_hour(hour)}\nYour Booking"
            disabled = True
            # Use custom HTML for user's own reservations
            st.markdown(f"""
            <div class="time-slot-my-reservation">
                {button_text}
            </div>
            """, unsafe_allow_html=True)
            continue
        elif is_reserved:
            # Obtener el nombre del usuario que reservó
            reserved_name = reservations_dict[hour]
            # Truncar el nombre si es muy largo
            if len(reserved_name) > 12:
                displayed_name = reserved_name[:9] + "..."
            else:
                displayed_name = reserved_name
            button_text = f"{format_hour(hour)}\n{displayed_name}"
            disabled = True
        elif is_past_hour:
            button_text = f"{format_hour(hour)}\nPast"
            disabled = True
        elif is_selected:
            # Use custom HTML for selected state
            st.markdown(f"""
            <div 
                style="
                    background:white;
                    border: 3px solid {US_OPEN_YELLOW};
                    color: {US_OPEN_BLUE};
                    padding: 2px;
                    border-radius: 6px;
                    text-align: center;
                    margin: 5px 0;
                    cursor: pointer;
                    font-weight: bold;
                    transform: scale(1);
                    box-shadow: 0 6px 12px rgba(0, 24, 84, 0.4);
                "
                onclick="document.querySelector('[data-testid=\\'baseButton-secondary\\'][key*=\\'hidden_{date}_{hour}\\']')?.click()"
            >
                {format_hour(hour)}<br>Selected
            </div>
            """, unsafe_allow_html=True)
            
            # Hidden button for functionality
            if st.button("Cancel", key=f"hidden_{date}_{hour}"):
                handle_time_slot_click(hour, date, current_user)
            continue
        elif is_selectable:
            button_text = f"{format_hour(hour)}\nAvailable"
            disabled = False
        else:
            button_text = f"{format_hour(hour)}\nUnavailable"
            disabled = True
        
        # Regular Streamlit button for non-selected states
        if st.button(
            button_text,
            key=f"hour_{date}_{hour}",
            disabled=disabled,
            use_container_width=True
        ):
            handle_time_slot_click(hour, date, current_user)

def handle_time_slot_click(hour, date, current_user):
    """Manejar clic en un slot de tiempo - ENHANCED with user validation"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)
    
    # Verificar límite de horas existentes del usuario
    user_existing_hours = db_manager.get_user_reservations_for_date(current_user['email'], date)
    
    # Si es una fecha diferente, limpiar selección anterior
    if selected_date is not None and selected_date != date:
        selected_hours = []
        selected_date = date
    
    if hour in selected_hours and selected_date == date:
        # Deseleccionar
        selected_hours.remove(hour)
        if not selected_hours:
            selected_date = None
    else:
        # Si no hay fecha seleccionada, establecer la fecha actual
        if selected_date is None:
            selected_date = date
            selected_hours = []
        
        # Verificar límite total de horas por día
        total_hours_after_selection = len(user_existing_hours) + len(selected_hours) + 1
        if total_hours_after_selection > 2:
            st.error(f"Maximum 2 hours per day. You already have {len(user_existing_hours)} hour(s) reserved.")
            return
        
        # Seleccionar (verificar límites)
        if len(selected_hours) >= 2:
            st.error("Maximum 2 hours per selection")
            return
        
        # Verificar que sea consecutiva si ya hay una hora seleccionada
        if selected_hours:
            existing_hour = selected_hours[0]
            if abs(hour - existing_hour) != 1:
                st.error("Selected hours must be consecutive")
                return
        
        selected_hours.append(hour)
    
    st.session_state.selected_hours = selected_hours
    st.session_state.selected_date = selected_date
    st.rerun()

# Inicializar estado de sesión
def init_reservation_session_state():
    """Inicializar estado de sesión"""
    if 'selected_hours' not in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None