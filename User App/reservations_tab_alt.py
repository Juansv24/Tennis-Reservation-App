"""
Streamlined Reservations Tab for Tennis Court Booking System
VERSION: Simplified & Efficient with US Open Styling
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
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"

def get_today_tomorrow():
    """Get today and tomorrow dates"""
    today = get_colombia_today()
    tomorrow = today + timedelta(days=1)
    return today, tomorrow

def get_current_hour():
    """Get current hour"""
    return get_colombia_now().hour

def format_hour(hour: int) -> str:
    """Format hour for display"""
    return f"{hour:02d}:00"

def format_date_short(date: datetime.date) -> str:
    """Format short date"""
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

def apply_streamlined_css():
    """Apply streamlined CSS with US Open styling"""
    st.markdown(f"""
    <style>
    /* Main App Container */
    .main-container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }}
    
    /* Header Styling */
    .user-header {{
        background: linear-gradient(135deg, {US_OPEN_BLUE} 0%, {US_OPEN_LIGHT_BLUE} 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
    }}
    
    .credits-display {{
        background: {US_OPEN_YELLOW};
        color: {US_OPEN_BLUE};
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
    }}
    
    /* Calendar Grid */
    .calendar-container {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin: 25px 0;
    }}
    
    .day-column {{
        background: #f8f9fa;
        border-radius: 12px;
        padding: 15px;
        border: 2px solid #e9ecef;
    }}
    
    .day-header {{
        background: {US_OPEN_LIGHT_BLUE};
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 1.1rem;
    }}
    
    /* Time Slot Styling */
    .time-slot {{
        margin: 8px 0;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 2px solid transparent;
    }}
    
    .slot-available {{
        background: white;
        border-color: {US_OPEN_LIGHT_BLUE};
        color: {US_OPEN_BLUE};
    }}
    
    .slot-available:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-color: {US_OPEN_YELLOW};
    }}
    
    .slot-selected {{
        background: #d4edda;
        border-color: #28a745;
        color: #155724;
        font-weight: bold;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
    }}
    
    .slot-reserved {{
        background: #f8f9fa;
        border-color: #dc3545;
        color: #dc3545;
        cursor: not-allowed;
        opacity: 0.7;
    }}
    
    .slot-my-reservation {{
        background: #d4edda;
        border-color: #28a745;
        color: #155724;
        font-weight: bold;
        cursor: not-allowed;
    }}
    
    .slot-unavailable {{
        background: #f5f5f5;
        border-color: #6c757d;
        color: #6c757d;
        cursor: not-allowed;
        opacity: 0.5;
    }}
    
    .slot-tennis-school {{
        background: #e3f2fd;
        border-color: #1976d2;
        color: #0d47a1;
        font-weight: bold;
        cursor: not-allowed;
    }}
    
    /* Confirmation Panel */
    .confirmation-panel {{
        background: linear-gradient(135deg, #f8f9fa 0%, white 100%);
        border: 2px solid {US_OPEN_LIGHT_BLUE};
        border-radius: 12px;
        padding: 25px;
        margin: 25px 0;
        text-align: center;
    }}
    
    .confirm-button {{
        background: {US_OPEN_BLUE} !important;
        color: white !important;
        border: none !important;
        padding: 15px 40px !important;
        border-radius: 8px !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }}
    
    .confirm-button:hover {{
        background: {US_OPEN_LIGHT_BLUE} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0,0,0,0.2) !important;
    }}
    
    /* Success Message */
    .success-message {{
        background: linear-gradient(135deg, #d4edda 0%, #f0fff0 100%);
        border: 2px solid #28a745;
        border-radius: 12px;
        padding: 25px;
        margin: 20px 0;
        color: #155724;
        text-align: center;
        animation: slideIn 0.5s ease-out;
    }}
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateY(-20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Control Buttons */
    .control-buttons {{
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }}
    
    .stButton > button {{
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}
    
    /* Selected Time Slot Buttons */
    button[key*="selected_"] {{
        background: #d4edda !important;
        border: 2px solid #28a745 !important;
        color: #155724 !important;
        font-weight: bold !important;
        transform: scale(1.02) !important;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4) !important;
    }}
    
    button[key*="selected_"]:hover {{
        background: #c3e6cb !important;
        transform: scale(1.04) !important;
    }}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .calendar-container {{
            grid-template-columns: 1fr;
        }}
        
        .main-container {{
            padding: 10px;
        }}
    }}
    
    /* Hide Streamlit Elements */
    .stDeployButton {{
        display: none;
    }}
    
    footer {{
        visibility: hidden;
    }}
    </style>
    """, unsafe_allow_html=True)

def show_reservation_tab():
    """Main reservation tab - streamlined version"""
    apply_streamlined_css()

    # Get current user
    current_user = get_current_user()
    if not current_user:
        st.error("Error de autenticación. Por favor actualiza la página.")
        return

    # Check if user can make reservations now
    can_reserve_now, reservation_time_error = db_manager.can_user_make_reservation_now(current_user['email'])

    if not can_reserve_now:
        show_read_only_view(current_user, reservation_time_error)
        return

    # Initialize session state
    init_reservation_session_state()

    # Get dates and current hour
    today, tomorrow = get_today_tomorrow()
    current_hour = get_current_hour()

    # Cache management
    cached_data = get_cached_reservation_data(today, tomorrow, current_user['email'])

    # Show main interface
    show_user_header(current_user)
    show_control_buttons()
    show_calendar_interface(today, tomorrow, cached_data, current_hour, current_user)
    show_confirmation_panel(current_user)

    # Show success message if reservation was just made
    if st.session_state.get('reservation_confirmed', False):
        show_success_message()
        st.session_state.reservation_confirmed = False

def show_user_header(current_user):
    """Show streamlined user header"""
    user_credits = db_manager.get_user_credits(current_user['email'])

    st.markdown(f"""
    <div class="user-header">
        <h2>🎾 ¡Hola, {current_user['full_name']}!</h2>
        <p>{current_user['email']}</p>
        <div class="credits-display">
            💰 {user_credits} Créditos Disponibles
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_control_buttons():
    """Show streamlined control buttons"""
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Actualizar", type="secondary", use_container_width=True):
            invalidate_reservation_cache()
            st.success("✅ Datos actualizados")
            st.rerun()

    with col2:
        if st.button("📋 Mis Reservas", type="secondary", use_container_width=True):
            st.session_state.show_my_reservations = not st.session_state.get('show_my_reservations', False)
            st.rerun()

    with col3:
        if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True):
            from auth_utils import logout_user
            logout_user()

def show_calendar_interface(today, tomorrow, cached_data, current_hour, current_user):
    """Show streamlined calendar interface"""

    # Show current reservations if toggled
    if st.session_state.get('show_my_reservations', False):
        show_my_current_reservations(today, tomorrow, cached_data)

    st.markdown("### 📅 Selecciona tu Horario")

    # Two-column layout for today and tomorrow
    col_today, col_tomorrow = st.columns(2)

    with col_today:
        st.markdown(f"""
        <div class="day-header">
            {format_date_short(today)}<br>
            <small>HOY</small>
        </div>
        """, unsafe_allow_html=True)

        show_day_schedule(today, cached_data['today'], current_user, True, current_hour)

    with col_tomorrow:
        st.markdown(f"""
        <div class="day-header">
            {format_date_short(tomorrow)}<br>
            <small>MAÑANA</small>
        </div>
        """, unsafe_allow_html=True)

        show_day_schedule(tomorrow, cached_data['tomorrow'], current_user, False, current_hour)

def show_day_schedule(date, day_data, current_user, is_today, current_hour):
    """Show schedule for a specific day"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)

    for hour in COURT_HOURS:
        # Check tennis school hours
        if is_tennis_school_hour(date, hour):
            st.markdown(f"""
            <div class="time-slot slot-tennis-school">
                {format_hour(hour)}<br>Escuela de Tenis
            </div>
            """, unsafe_allow_html=True)
            continue

        # Determine slot state
        is_reserved = hour in day_data['reservations']
        is_my_reservation = hour in day_data['user_reservations']
        is_selected = hour in selected_hours and selected_date == date
        is_past_hour = is_today and hour < current_hour
        is_selectable = not is_reserved and not is_past_hour and not is_my_reservation

        # Render slot based on state
        if is_my_reservation:
            st.markdown(f"""
            <div class="time-slot slot-my-reservation">
                {format_hour(hour)}<br>Tu Reserva
            </div>
            """, unsafe_allow_html=True)

        elif is_reserved:
            reserved_name = day_data['reservation_names'][hour]
            display_name = reserved_name[:9] + "..." if len(reserved_name) > 12 else reserved_name
            st.markdown(f"""
            <div class="time-slot slot-reserved">
                {format_hour(hour)}<br>{display_name}
            </div>
            """, unsafe_allow_html=True)

        elif is_past_hour:
            st.markdown(f"""
            <div class="time-slot slot-unavailable">
                {format_hour(hour)}<br>Pasado
            </div>
            """, unsafe_allow_html=True)

        elif is_selected:
            # Use a regular button but style it with CSS classes
            if st.button(
                f"✅ {format_hour(hour)}\nSeleccionado",
                key=f"selected_{date}_{hour}",
                use_container_width=True,
                type="secondary"
            ):
                handle_time_slot_click(hour, date, current_user)

        elif is_selectable:
            if st.button(f"✅ {format_hour(hour)}\nDisponible", key=f"select_{date}_{hour}", use_container_width=True):
                handle_time_slot_click(hour, date, current_user)

        else:
            st.markdown(f"""
            <div class="time-slot slot-unavailable">
                {format_hour(hour)}<br>No Disponible
            </div>
            """, unsafe_allow_html=True)

def show_confirmation_panel(current_user):
    """Show streamlined confirmation panel"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)

    if not selected_hours or selected_date is None:
        # Show simple instructions
        st.markdown("""
        <div class="confirmation-panel">
            <h3>🎯 Cómo Reservar</h3>
            <p>1. <strong>Selecciona</strong> los horarios disponibles (máximo 2 horas por día)</p>
            <p>2. <strong>Confirma</strong> tu reserva con un click</p>
            <p>3. <strong>Recibe</strong> confirmación por email</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Show confirmation details
    sorted_hours = sorted(selected_hours)
    start_time = format_hour(min(sorted_hours))
    end_time = format_hour(max(sorted_hours) + 1)

    st.markdown(f"""
    <div class="confirmation-panel">
        <h3>✅ Confirmar Reserva</h3>
        <p><strong>Fecha:</strong> {format_date_full(selected_date)}</p>
        <p><strong>Horario:</strong> {start_time} - {end_time}</p>
        <p><strong>Duración:</strong> {len(selected_hours)} hora(s)</p>
        <p><strong>Créditos a usar:</strong> {len(selected_hours)}</p>
    </div>
    """, unsafe_allow_html=True)

    # Confirmation button
    if st.button(
        "🎾 CONFIRMAR RESERVA",
        type="primary",
        use_container_width=True,
        key="confirm_reservation"
    ):
        handle_reservation_confirmation(current_user, selected_date, selected_hours)

def show_my_current_reservations(today, tomorrow, cached_data):
    """Show current user reservations"""
    user_today = cached_data['today']['user_reservations']
    user_tomorrow = cached_data['tomorrow']['user_reservations']

    if not user_today and not user_tomorrow:
        st.info("📅 No tienes reservas programadas")
        return

    st.markdown("### 📋 Tus Reservas Actuales")

    if user_today:
        st.write(f"**Hoy ({format_date_short(today)}):**")
        for hour in sorted(user_today):
            st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")

    if user_tomorrow:
        st.write(f"**Mañana ({format_date_short(tomorrow)}):**")
        for hour in sorted(user_tomorrow):
            st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")

def show_read_only_view(current_user, time_error):
    """Show read-only view when reservations are not allowed"""
    show_user_header(current_user)

    st.error(f"🕐 {time_error}")

    # Show simple schedule view
    today, tomorrow = get_today_tomorrow()
    cached_data = get_cached_reservation_data(today, tomorrow, current_user['email'])

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            from auth_utils import logout_user
            logout_user()

    st.markdown("### 👁️ Vista de Disponibilidad")
    show_calendar_interface(today, tomorrow, cached_data, get_current_hour(), current_user)

def handle_time_slot_click(hour, date, current_user):
    """Handle time slot selection/deselection"""
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)

    # Get user existing reservations from cache
    today, tomorrow = get_today_tomorrow()
    cached_data = get_cached_reservation_data(today, tomorrow, current_user['email'])

    if date == today:
        user_existing_hours = cached_data['today']['user_reservations']
    else:
        user_existing_hours = cached_data['tomorrow']['user_reservations']

    # Handle deselection
    if hour in selected_hours and selected_date == date:
        selected_hours.remove(hour)
        if not selected_hours:
            selected_date = None
        st.session_state.selected_hours = selected_hours
        st.session_state.selected_date = selected_date
        st.rerun()
        return

    # Handle new selection
    if selected_date is not None and selected_date != date:
        selected_hours = []
        selected_date = date

    if selected_date is None:
        selected_date = date
        selected_hours = []

    # Validate selection
    if not validate_selection(hour, date, selected_hours, user_existing_hours, current_user):
        return

    selected_hours.append(hour)
    st.session_state.selected_hours = selected_hours
    st.session_state.selected_date = selected_date
    st.rerun()

def validate_selection(hour, date, selected_hours, user_existing_hours, current_user):
    """Validate if selection is allowed"""
    # Check daily limit
    total_hours_after_selection = len(user_existing_hours) + len(selected_hours) + 1
    if total_hours_after_selection > 2:
        st.error(f"⚠️ Máximo 2 horas por día. Ya tienes {len(user_existing_hours)} hora(s) reservada(s).")
        return False

    # Check selection limit
    if len(selected_hours) >= 2:
        st.error("⚠️ Máximo 2 horas por selección")
        return False

    # Check credits
    credits_needed = len(selected_hours) + 1
    user_credits = db_manager.get_user_credits(current_user['email'])
    if user_credits < credits_needed:
        st.error(f"💰 Créditos insuficientes. Necesitas {credits_needed}, tienes {user_credits}.")
        return False

    # Check consecutive hours
    if selected_hours:
        existing_hour = selected_hours[0]
        if abs(hour - existing_hour) != 1:
            st.error("⚠️ Las horas seleccionadas deben ser consecutivas")
            return False

    # Check consecutive days conflict
    if validate_consecutive_days_conflict(hour, date, current_user):
        return False

    return True

def validate_consecutive_days_conflict(hour, date, current_user):
    """Validate consecutive days conflict"""
    today, tomorrow = get_today_tomorrow()
    cached_data = get_cached_reservation_data(today, tomorrow, current_user['email'])

    user_today = cached_data['today']['user_reservations']
    user_tomorrow = cached_data['tomorrow']['user_reservations']

    if date == today and hour in user_tomorrow:
        st.error(f"⚠️ No puedes reservar a las {format_hour(hour)} hoy porque ya lo tienes reservado mañana.")
        return True
    elif date == tomorrow and hour in user_today:
        st.error(f"⚠️ No puedes reservar a las {format_hour(hour)} mañana porque ya lo tienes reservado hoy.")
        return True

    return False

def handle_reservation_confirmation(current_user, date, selected_hours):
    """Handle reservation confirmation with transaction safety"""
    successful_reservations = []

    with st.spinner("Procesando reserva..."):
        for hour in selected_hours:
            if create_reservation_with_transaction(current_user, date, hour):
                successful_reservations.append(hour)

    if len(successful_reservations) == len(selected_hours):
        # Complete success
        st.session_state.reservation_confirmed = True
        st.session_state.last_reservation_data = {
            'name': current_user['full_name'],
            'date': date,
            'hours': successful_reservations,
            'credits_used': len(successful_reservations)
        }

        # Clear selection and refresh cache
        st.session_state.selected_hours = []
        st.session_state.selected_date = None
        invalidate_reservation_cache()

        # Send confirmation email
        send_reservation_confirmation_email(current_user, date, successful_reservations)
        st.balloons()
        st.rerun()
    else:
        st.error("❌ Error al procesar la reserva. Por favor intenta de nuevo.")

def create_reservation_with_transaction(current_user, date, hour):
    """Create reservation with atomic transaction"""
    try:
        # Check availability
        if not db_manager.is_hour_available(date, hour):
            return False

        # Check credits
        if db_manager.get_user_credits(current_user['email']) < 1:
            return False

        # Create reservation
        if not db_manager.save_reservation(date, hour, current_user['full_name'], current_user['email']):
            return False

        # Deduct credit
        if not db_manager.use_credits_for_reservation(current_user['email'], 1, date.strftime('%Y-%m-%d'), hour):
            # Rollback reservation
            db_manager.delete_reservation(date.strftime('%Y-%m-%d'), hour)
            return False

        return True
    except Exception:
        return False

def send_reservation_confirmation_email(current_user, date, selected_hours):
    """Send reservation confirmation email"""
    try:
        if not email_manager.is_configured():
            st.info("📧 Servicio de email no configurado - reserva guardada sin confirmación")
            return

        date_datetime = datetime.datetime.combine(date, datetime.datetime.min.time())
        success, message = email_manager.send_reservation_confirmation(
            current_user['email'],
            current_user['full_name'],
            date_datetime,
            selected_hours,
            {}
        )

        if success:
            st.success("📧 ¡Email de confirmación enviado!")
        else:
            st.warning(f"⚠️ Reserva guardada pero falló el email: {message}")
    except Exception as e:
        st.warning("⚠️ Reserva guardada pero falló la notificación por email")

def show_success_message():
    """Show reservation success message"""
    if not st.session_state.get('last_reservation_data'):
        return

    data = st.session_state.last_reservation_data
    remaining_credits = db_manager.get_user_credits(st.session_state.user_info['email'])

    sorted_hours = sorted(data['hours'])
    start_time = format_hour(min(sorted_hours))
    end_time = format_hour(max(sorted_hours) + 1)

    st.markdown(f"""
    <div class="success-message">
        <h3>🎉 ¡Reserva Confirmada!</h3>
        <p><strong>Nombre:</strong> {data['name']}</p>
        <p><strong>Fecha:</strong> {format_date_full(data['date'])}</p>
        <p><strong>Horario:</strong> {start_time} - {end_time}</p>
        <p><strong>Duración:</strong> {len(sorted_hours)} hora(s)</p>
        <p><strong>💰 Créditos usados:</strong> {data['credits_used']}</p>
        <p><strong>💳 Créditos restantes:</strong> {remaining_credits}</p>
        <p>📧 <em>Email de confirmación enviado</em></p>
    </div>
    """, unsafe_allow_html=True)

    # Clear data after showing
    if 'last_reservation_data' in st.session_state:
        del st.session_state['last_reservation_data']

def get_cached_reservation_data(today, tomorrow, user_email):
    """Get cached reservation data with 30-second cache"""
    cache_key = f"reservations_cache_{today}_{tomorrow}"
    cache_timestamp_key = f"cache_timestamp_{today}_{tomorrow}"

    current_time = time.time()
    should_refresh = (
        cache_key not in st.session_state or
        cache_timestamp_key not in st.session_state or
        current_time - st.session_state[cache_timestamp_key] > 30
    )

    if should_refresh:
        summary = db_manager.get_date_reservations_summary([today, tomorrow], user_email)

        today_str = today.strftime('%Y-%m-%d')
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')

        cached_data = {
            'today': {
                'reservations': summary['all_reservations'].get(today_str, []),
                'user_reservations': summary['user_reservations'].get(today_str, []),
                'reservation_names': summary['reservation_names'].get(today_str, {})
            },
            'tomorrow': {
                'reservations': summary['all_reservations'].get(tomorrow_str, []),
                'user_reservations': summary['user_reservations'].get(tomorrow_str, []),
                'reservation_names': summary['reservation_names'].get(tomorrow_str, {})
            }
        }

        st.session_state[cache_key] = cached_data
        st.session_state[cache_timestamp_key] = current_time
    else:
        cached_data = st.session_state[cache_key]

    return cached_data

def is_tennis_school_hour(date, hour):
    """Check if it's tennis school hour (weekends 8-12)"""
    if date.weekday() not in [5, 6]:  # Not weekend
        return False
    return 8 <= hour <= 11

def init_reservation_session_state():
    """Initialize reservation session state"""
    if 'selected_hours' not in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None
    if 'show_my_reservations' not in st.session_state:
        st.session_state.show_my_reservations = False

def invalidate_reservation_cache():
    """Force cache refresh"""
    today, tomorrow = get_today_tomorrow()
    cache_key = f"reservations_cache_{today}_{tomorrow}"
    cache_timestamp_key = f"cache_timestamp_{today}_{tomorrow}"

    if cache_key in st.session_state:
        del st.session_state[cache_key]
    if cache_timestamp_key in st.session_state:
        del st.session_state[cache_timestamp_key]