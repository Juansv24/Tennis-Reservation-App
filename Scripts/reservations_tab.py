"""
Pestaña de Reservas para Sistema de Reservas de Cancha de Tenis
VERSIÓN ACTUALIZADA con Integración de Autenticación
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
    """Aplicar CSS personalizado con colores US Open"""
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
        st.error("Error de autenticación. Por favor actualiza la página.")
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
    st.subheader("Detalles de la Reserva")

    # Mostrar información del usuario
    st.markdown(f"""
    <div class="user-info-display">
        <strong>👤 Reservando como:</strong><br>
        {current_user['full_name']}<br>
        <small>{current_user['email']}</small>
    </div>
    """, unsafe_allow_html=True)

    # Mostrar reservas existentes del usuario
    show_user_existing_reservations(today_date, tomorrow_date, user_today_reservations, user_tomorrow_reservations)

    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)

    # Mostrar reglas de reserva
    with st.expander("📋 Reglas de Reserva"):
        st.markdown("""
        • **Solo se puede hacer reservar para hoy y para mañana**  
        • **Máximo 2 horas** por persona por día. 
        • **Horas consecutivas** requeridas si se reservan 2 horas
        • **Horario de cancha:** 6:00 AM - 9:00 PM  
        """)

    # Mostrar selección actual
    if selected_hours and selected_date is not None:
        st.markdown("### Nueva Selección")

        st.write(f"**Fecha:** {format_date_full(selected_date)}")
        st.write(f"**Slots de Tiempo:** {len(selected_hours)} hora(s)")

        for hour in sorted(selected_hours):
            st.write(f"• {format_hour(hour)} - {format_hour(hour + 1)}")

        if len(selected_hours) > 1:
            start_time = format_hour(min(selected_hours))
            end_time = format_hour(max(selected_hours) + 1)
            st.write(f"**Tiempo Total:** {start_time} - {end_time}")

        st.divider()

        # Formulario simplificado (sin nombre y email)
        st.markdown("### Confirmar Reserva")

        # Mostrar resumen de la reserva
        st.info(f"Reservando para: **{current_user['full_name']}** ({current_user['email']})")

        if st.button("✅ Confirmar Reserva", type="primary", use_container_width=True):
            handle_reservation_submission(current_user, selected_date, selected_hours)

    else:
        st.info("Selecciona los horarios disponibles en el calendario para continuar")

        st.markdown("### Cómo Reservar")
        st.write("1. **Selecciona los horarios disponibles que desees entre hoy y mañana (hasta 2 horas)")
        st.write("2. **Confirma tu reserva** con un click")

def show_user_existing_reservations(today_date, tomorrow_date, user_today_reservations, user_tomorrow_reservations):
    """Mostrar reservas existentes del usuario"""
    has_reservations = bool(user_today_reservations or user_tomorrow_reservations)

    if has_reservations:
        st.markdown("### Tus Reservas Actuales")

        if user_today_reservations:
            st.write(f"**Hoy ({format_date_short(today_date)}):** {len(user_today_reservations)} hora(s)")
            for hour in sorted(user_today_reservations):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")

        if user_tomorrow_reservations:
            st.write(f"**Mañana ({format_date_short(tomorrow_date)}):** {len(user_tomorrow_reservations)} hora(s)")
            for hour in sorted(user_tomorrow_reservations):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")

        st.divider()

def handle_reservation_submission(current_user, date, selected_hours):
    """Manejar el envío de la reserva con autenticación"""

    # Validar límite de horas
    if len(selected_hours) > 2:
        st.error("Máximo 2 horas por día")
        return

    # Verificar que las horas sean consecutivas (si hay más de una)
    if len(selected_hours) > 1:
        sorted_hours = sorted(selected_hours)
        for i in range(1, len(sorted_hours)):
            if sorted_hours[i] - sorted_hours[i-1] != 1:
                st.error("Las horas seleccionadas deben ser consecutivas")
                return

    # Verificar límite por usuario (máximo 2 horas por día)
    user_existing_hours = db_manager.get_user_reservations_for_date(current_user['email'], date)
    if len(user_existing_hours) + len(selected_hours) > 2:
        st.error(f"Solo puedes reservar 2 horas por día. Ya tienes {len(user_existing_hours)} hora(s) reservada(s).")
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

        # Enviar email de confirmación
        send_reservation_confirmation_email(current_user, date, selected_hours)

        st.session_state.selected_hours = []
        st.session_state.selected_date = None
        st.balloons()

    elif success_count > 0:
        # Éxito parcial
        st.warning(f"Se reservaron {success_count} hora(s). Las siguientes ya estaban ocupadas: {', '.join(format_hour(h) for h in failed_hours)}")
        st.session_state.selected_hours = failed_hours

    else:
        # Falló completamente
        st.error("No se pudo hacer la reserva. Todos los slots seleccionados ya están ocupados.")

def send_reservation_confirmation_email(current_user, date, selected_hours):
    """Enviar email de confirmación de reserva"""
    try:
        # Verificar primero si el servicio de email está configurado
        if not email_manager.is_configured():
            st.info("📧 Servicio de email no configurado - reserva guardada sin confirmación por email")
            return

        # Convertir fecha a datetime para email
        date_datetime = datetime.datetime.combine(date, datetime.datetime.min.time())

        success, message = email_manager.send_reservation_confirmation(
            current_user['email'],
            current_user['full_name'],
            date_datetime,
            selected_hours,
            {}  # Detalles adicionales de reserva si se necesitan
        )

        if success:
            st.success("📧 ¡Email de confirmación enviado!")
        else:
            st.warning(f"⚠️ Reserva guardada pero falló el email: {message}")
            # Mostrar el error específico para depuración
            with st.expander("Detalles del Error de Email"):
                st.write(message)

    except Exception as e:
        st.warning("⚠️ Reserva guardada pero falló la notificación por email")
        # Mostrar detalles del error para depuración
        with st.expander("Detalles del Error"):
            st.write(f"Error: {str(e)}")
        st.info("💡 Tu reserva está confirmada aún sin el email")

def show_success_message(name, date_obj, selected_hours):
    """Mostrar mensaje de éxito"""
    sorted_hours = sorted(selected_hours)
    start_time = format_hour(min(sorted_hours))
    end_time = format_hour(max(sorted_hours) + 1)

    st.markdown(f"""
    <div class="success-message">
        <h3>✅ ¡Reserva Confirmada!</h3>
        <p><strong>Nombre:</strong> {name}</p>
        <p><strong>Fecha:</strong> {format_date_full(date_obj)}</p>
        <p><strong>Hora:</strong> {start_time} - {end_time}</p>
        <p><strong>Duración:</strong> {len(sorted_hours)} hora(s)</p>
    </div>
    """, unsafe_allow_html=True)

def show_calendar_view(today, tomorrow, today_reservations, tomorrow_reservations, current_hour, current_user):
    """Mostrar vista de calendario"""
    st.subheader("Disponibilidad de la Cancha")

    # Crear dos columnas para los dos días
    today_col, tomorrow_col = st.columns(2)

    # Columna de hoy
    with today_col:
        st.markdown(f"""
        <div class="calendar-header">
            {format_date_short(today)}<br>
            <small>HOY</small>
        </div>
        """, unsafe_allow_html=True)

        show_day_schedule(today, today_reservations, current_user, is_today=True, current_hour=current_hour)

    # Columna de mañana
    with tomorrow_col:
        st.markdown(f"""
        <div class="calendar-header">
            {format_date_short(tomorrow)}<br>
            <small>MAÑANA</small>
        </div>
        """, unsafe_allow_html=True)

        show_day_schedule(tomorrow, tomorrow_reservations, current_user, is_today=False, current_hour=current_hour)

def show_day_schedule(date, reservations_dict, current_user, is_today=False, current_hour=None):
    """Mostrar horarios para un día específico"""
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
            button_text = f"{format_hour(hour)}\nTu Reserva"
            disabled = True
            # Usar HTML personalizado para las propias reservas del usuario
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
            button_text = f"{format_hour(hour)}\nPasado"
            disabled = True
        elif is_selected:
            # Usar HTML personalizado para estado seleccionado
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
                {format_hour(hour)}<br>Seleccionado
            </div>
            """, unsafe_allow_html=True)

            # Botón oculto para funcionalidad
            if st.button("Cancelar", key=f"hidden_{date}_{hour}"):
                handle_time_slot_click(hour, date, current_user)
            continue
        elif is_selectable:
            button_text = f"{format_hour(hour)}\nDisponible"
            disabled = False
        else:
            button_text = f"{format_hour(hour)}\nNo Disponible"
            disabled = True

        # Botón regular de Streamlit para estados no seleccionados
        if st.button(
            button_text,
            key=f"hour_{date}_{hour}",
            disabled=disabled,
            use_container_width=True
        ):
            handle_time_slot_click(hour, date, current_user)

def handle_time_slot_click(hour, date, current_user):
    """Manejar clic en un slot de tiempo con validación de usuario"""
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
            st.error(f"Máximo 2 horas por día. Ya tienes {len(user_existing_hours)} hora(s) reservada(s).")
            return

        # Seleccionar (verificar límites)
        if len(selected_hours) >= 2:
            st.error("Máximo 2 horas por selección")
            return

        # Verificar que sea consecutiva si ya hay una hora seleccionada
        if selected_hours:
            existing_hour = selected_hours[0]
            if abs(hour - existing_hour) != 1:
                st.error("Las horas seleccionadas deben ser consecutivas")
                return

        selected_hours.append(hour)

    st.session_state.selected_hours = selected_hours
    st.session_state.selected_date = selected_date
    st.rerun()

def init_reservation_session_state():
    """Inicializar estado de sesión para reservas"""
    if 'selected_hours' not in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None