"""
Simplified Reservations Tab for Tennis Court Booking System
Clean, card-based interface with minimal code
"""
import time
import streamlit as st
import datetime
from datetime import timedelta
from database_manager import db_manager
from auth_utils import get_current_user
from timezone_utils import get_colombia_today, get_colombia_now
from email_config import email_manager

# Configuration
COURT_HOURS = list(range(6, 22))  # 6 AM to 9 PM

def get_dates():
    """Get today and tomorrow"""
    today = get_colombia_today()
    tomorrow = today + timedelta(days=1)
    return today, tomorrow

def format_hour(hour: int) -> str:
    """Format hour for display"""
    return f"{hour:02d}:00"

def format_date_display(date: datetime.date) -> str:
    """Format date for display"""
    days = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']
    months = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN',
              'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
    day_name = days[date.weekday()]
    month_name = months[date.month - 1]
    return f"{day_name} {date.day} {month_name}"

def format_date_full(date: datetime.date) -> str:
    """Format full date"""
    days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    day_name = days[date.weekday()]
    month_name = months[date.month - 1]
    return f"{day_name}, {date.day} de {month_name} de {date.year}"

def apply_styles():
    """Apply minimal CSS styles"""
    st.markdown("""
    <style>
    .time-card {
        border-radius: 12px;
        padding: 16px;
        margin: 6px 0;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        min-height: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .time-card.available {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border: 2px solid #2478CC;
        color: #001854;
    }
    .time-card.available:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(36, 120, 204, 0.3);
    }
    .time-card.selected {
        background: linear-gradient(135deg, #FFD400 0%, #FFF59D 100%);
        border: 3px solid #001854;
        color: #001854;
        font-weight: bold;
    }
    .time-card.reserved {
        background: #ffebee;
        border: 2px solid #e57373;
        color: #c62828;
        cursor: default;
    }
    .time-card.my-reservation {
        background: #e8f5e8;
        border: 3px solid #4CAF50;
        color: #2e7d32;
        font-weight: bold;
        cursor: default;
    }
    .time-card.unavailable {
        background: #f5f5f5;
        border: 1px solid #e0e0e0;
        color: #757575;
        cursor: default;
        opacity: 0.6;
    }
    .selection-summary {
        background: linear-gradient(135deg, #FFD400 0%, #FFF59D 100%);
        border: 2px solid #001854;
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
        text-align: center;
        box-shadow: 0 4px 12px rgba(255, 212, 0, 0.3);
    }
    .user-info {
        background: #f0f8ff;
        border: 1px solid #2478CC;
        border-radius: 8px;
        padding: 12px;
        margin: 12px 0;
        color: #001854;
    }
    </style>
    """, unsafe_allow_html=True)

def get_reservation_data():
    """Get cached reservation data"""
    today, tomorrow = get_dates()
    cache_key = f"reservations_{today}_{tomorrow}"
    cache_time_key = f"cache_time_{today}_{tomorrow}"

    current_time = time.time()
    if (cache_key not in st.session_state or
        cache_time_key not in st.session_state or
        current_time - st.session_state[cache_time_key] > 30):

        # Refresh data
        current_user = get_current_user()
        summary = db_manager.get_date_reservations_summary([today, tomorrow], current_user['email'])

        today_str = today.strftime('%Y-%m-%d')
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')

        st.session_state[cache_key] = {
            'today_reservations': summary['reservation_names'].get(today_str, {}),
            'tomorrow_reservations': summary['reservation_names'].get(tomorrow_str, {}),
            'user_today': summary['user_reservations'].get(today_str, []),
            'user_tomorrow': summary['user_reservations'].get(tomorrow_str, [])
        }
        st.session_state[cache_time_key] = current_time

    return st.session_state[cache_key]

def create_time_slot_card(hour, date, reservations, user_reservations, current_hour):
    """Create interactive time slot card"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date')

    is_reserved = hour in reservations
    is_my_reservation = hour in user_reservations
    is_selected = hour in selected_hours and selected_date == date
    is_past = date == get_dates()[0] and current_hour and hour < current_hour

    # Determine card type and content
    if is_my_reservation:
        card_type = "my-reservation"
        subtitle = "Tu Reserva"
        clickable = False
    elif is_reserved:
        card_type = "reserved"
        name = reservations[hour]
        subtitle = f"Reservado por {name[:12]}{'...' if len(name) > 12 else ''}"
        clickable = False
    elif is_past:
        card_type = "unavailable"
        subtitle = "No disponible"
        clickable = False
    elif is_selected:
        card_type = "selected"
        subtitle = "Seleccionado ✓"
        clickable = True
    else:
        card_type = "available"
        subtitle = "Disponible"
        clickable = True

    # Create card HTML
    card_html = f"""
    <div class="time-card {card_type}" onclick="document.getElementById('slot_{date}_{hour}').click()">
        <div style="font-size: 16px; font-weight: bold;">{format_hour(hour)}</div>
        <div style="font-size: 12px; opacity: 0.8;">{subtitle}</div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    # Hidden button for functionality
    if clickable:
        if st.button("", key=f"slot_{date}_{hour}", help=f"Click para {'deseleccionar' if is_selected else 'seleccionar'}"):
            handle_slot_click(hour, date)

def handle_slot_click(hour, date):
    """Handle time slot selection"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date')
    current_user = get_current_user()

    # Get user's existing reservations for validation
    data = get_reservation_data()
    today, tomorrow = get_dates()
    user_existing = data['user_today'] if date == today else data['user_tomorrow']
    user_other_day = data['user_tomorrow'] if date == today else data['user_today']

    # If different date selected, clear previous selection
    if selected_date and selected_date != date:
        selected_hours = []

    selected_date = date

    if hour in selected_hours:
        # Deselect
        selected_hours.remove(hour)
        if not selected_hours:
            selected_date = None
    else:
        # Validate selection
        if len(user_existing) + len(selected_hours) + 1 > 2:
            st.error(f"Máximo 2 horas por día. Ya tienes {len(user_existing)} hora(s) reservada(s).")
            return

        if hour in user_other_day:
            other_day = "mañana" if date == today else "hoy"
            st.error(f"No puedes reservar a las {format_hour(hour)} porque ya lo tienes reservado {other_day}.")
            return

        if len(selected_hours) >= 2:
            st.error("Máximo 2 horas por selección")
            return

        if selected_hours and abs(hour - selected_hours[0]) != 1:
            st.error("Las horas seleccionadas deben ser consecutivas")
            return

        selected_hours.append(hour)

    st.session_state.selected_hours = selected_hours
    st.session_state.selected_date = selected_date
    st.rerun()

def show_selection_summary():
    """Show current selection summary"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date')

    if selected_hours and selected_date:
        sorted_hours = sorted(selected_hours)
        start_time = format_hour(min(sorted_hours))
        end_time = format_hour(max(sorted_hours) + 1)
        date_display = format_date_display(selected_date)

        st.markdown(f"""
        <div class="selection-summary">
            <div style="font-size: 16px; font-weight: bold; color: #001854; margin-bottom: 8px;">
                📅 Selección Actual
            </div>
            <div style="color: #001854;">
                <strong>{date_display}</strong> • {start_time} - {end_time} • {len(sorted_hours)} hora(s)
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_confirmation_section(current_user):
    """Show confirmation section"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date')

    if selected_hours and selected_date:
        show_selection_summary()

        st.markdown("### ✅ Confirmar Reserva")

        st.markdown(f"""
        <div class="user-info">
            <strong>Reservando para:</strong> {current_user['full_name']}<br>
            <small>{current_user['email']}</small>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🎾 CONFIRMAR RESERVA", type="primary", use_container_width=True):
                process_reservation(current_user, selected_date, selected_hours)

        with col2:
            if st.button("🗑️ Limpiar Selección", type="secondary", use_container_width=True):
                st.session_state.selected_hours = []
                st.session_state.selected_date = None
                st.rerun()
    else:
        st.markdown("""
        ### 📋 Cómo Reservar
        1. **Haz clic** en los horarios disponibles (máximo 2 horas)
        2. **Confirma** tu selección
        
        💡 *Los horarios seleccionados se destacan en amarillo*
        """)

def process_reservation(current_user, date, selected_hours):
    """Process the reservation"""
    # Validate availability in real-time
    with st.spinner("Verificando disponibilidad..."):
        unavailable = [h for h in selected_hours if not db_manager.is_hour_available(date, h)]

    if unavailable:
        hour_list = ", ".join([format_hour(h) for h in unavailable])
        st.error(f"Los siguientes horarios ya fueron reservados: {hour_list}")
        # Remove unavailable hours and refresh
        st.session_state.selected_hours = [h for h in selected_hours if h not in unavailable]
        if not st.session_state.selected_hours:
            st.session_state.selected_date = None
        clear_cache()
        st.rerun()
        return

    # Attempt reservation
    success_count = 0
    with st.spinner("Procesando reserva..."):
        for hour in selected_hours:
            if db_manager.save_reservation(date, hour, current_user['full_name'], current_user['email']):
                success_count += 1

    if success_count == len(selected_hours):
        show_success_message(current_user['full_name'], date, selected_hours)
        send_confirmation_email(current_user, date, selected_hours)
        st.session_state.selected_hours = []
        st.session_state.selected_date = None
        clear_cache()
        st.balloons()
    else:
        st.error("No se pudo completar la reserva")
        clear_cache()

def show_success_message(name, date_obj, selected_hours):
    """Show success message"""
    sorted_hours = sorted(selected_hours)
    start_time = format_hour(min(sorted_hours))
    end_time = format_hour(max(sorted_hours) + 1)

    st.markdown(f"""
    <div style="background: #e8f5e8; border: 2px solid #4CAF50; border-radius: 12px; 
                padding: 20px; margin: 20px 0; color: #2e7d32; text-align: center;">
        <h3>✅ ¡Reserva Confirmada!</h3>
        <p><strong>Nombre:</strong> {name}</p>
        <p><strong>Fecha:</strong> {format_date_full(date_obj)}</p>
        <p><strong>Hora:</strong> {start_time} - {end_time}</p>
        <p><strong>Duración:</strong> {len(sorted_hours)} hora(s)</p>
    </div>
    """, unsafe_allow_html=True)

def send_confirmation_email(current_user, date, selected_hours):
    """Send confirmation email if configured"""
    try:
        if email_manager.is_configured():
            date_datetime = datetime.datetime.combine(date, datetime.datetime.min.time())
            success, message = email_manager.send_reservation_confirmation(
                current_user['email'], current_user['full_name'],
                date_datetime, selected_hours, {}
            )
            if success:
                st.success("📧 ¡Email de confirmación enviado!")
            else:
                st.warning("⚠️ Reserva guardada pero falló el email")
    except Exception:
        st.info("💡 Reserva confirmada (sin notificación por email)")

def clear_cache():
    """Clear reservation cache"""
    today, tomorrow = get_dates()
    cache_key = f"reservations_{today}_{tomorrow}"
    cache_time_key = f"cache_time_{today}_{tomorrow}"
    if cache_key in st.session_state:
        del st.session_state[cache_key]
    if cache_time_key in st.session_state:
        del st.session_state[cache_time_key]

def show_user_reservations(data):
    """Show user's existing reservations"""
    today, tomorrow = get_dates()
    user_today = data['user_today']
    user_tomorrow = data['user_tomorrow']

    if user_today or user_tomorrow:
        st.markdown("### Tus Reservas Actuales")

        if user_today:
            st.write(f"**Hoy ({format_date_display(today)}):** {len(user_today)} hora(s)")
            for hour in sorted(user_today):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")

        if user_tomorrow:
            st.write(f"**Mañana ({format_date_display(tomorrow)}):** {len(user_tomorrow)} hora(s)")
            for hour in sorted(user_tomorrow):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")

        st.divider()

def show_reservation_tab():
    """Main reservation interface"""
    apply_styles()

    current_user = get_current_user()
    if not current_user:
        st.error("Error de autenticación")
        return

    # Get data
    data = get_reservation_data()
    today, tomorrow = get_dates()
    current_hour = get_colombia_now().hour

    # Show user info
    st.markdown(f"""
    <div class="user-info">
        <strong>👤 Reservando como:</strong> {current_user['full_name']}<br>
        <small>{current_user['email']}</small>
    </div>
    """, unsafe_allow_html=True)

    # Show existing reservations
    show_user_reservations(data)

    # Calendar view
    st.subheader("🎾 Disponibilidad de la Cancha")

    col1, col2 = st.columns(2)

    # Today column
    with col1:
        st.markdown(f"**{format_date_display(today)} - HOY**")
        for hour in COURT_HOURS:
            create_time_slot_card(hour, today, data['today_reservations'],
                                data['user_today'], current_hour)

    # Tomorrow column
    with col2:
        st.markdown(f"**{format_date_display(tomorrow)} - MAÑANA**")
        for hour in COURT_HOURS:
            create_time_slot_card(hour, tomorrow, data['tomorrow_reservations'],
                                data['user_tomorrow'], None)

    st.divider()

    # Confirmation section
    show_confirmation_section(current_user)

def init_reservation_session_state():
    """Initialize session state"""
    if 'selected_hours' not in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None