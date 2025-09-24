"""
Pestaña de Reservas para Sistema de Reservas de Cancha de Tenis
VERSIÓN ACTUALIZADA con Integración de Autenticación
"""
import time
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
        /* Target all buttons within the big-confirm-button class */
    .big-confirm-button button {{
        font-size: 2rem !important;
        padding: 20px 40px !important;
        height: 70px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        min-height: 70px !important;
    }}
    
    /* More specific targeting for Streamlit's button structure */
    div[data-testid="stButton"] button[kind="primary"] {{
        font-size: 2rem !important;
        padding: 20px 40px !important;
        height: 70px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        min-height: 70px !important;
    }}
    
    /* Even more specific - target by the button key */
    button[key="big_confirm_btn"] {{
        font-size: 2rem !important;
        padding: 20px 40px !important;
        height: 70px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        min-height: 70px !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def show_user_controls_bar():
    """Mostrar barra de controles para usuario - versión minimalista"""
    from auth_utils import logout_user

    # Crear 2 columnas iguales para los botones
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Actualizar Datos", type="secondary", use_container_width=True, key="user_refresh_btn"):
            invalidate_reservation_cache()
            st.success("✅ Datos actualizados")
            st.rerun()

    with col2:
        if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True, key="user_logout_btn"):
            logout_user()

def show_read_only_schedule_view(current_user):
    """Mostrar vista de solo lectura cuando no se pueden hacer reservas"""

    today, tomorrow = get_today_tomorrow()

    # Mostrar barra de controles (solo actualizar y logout)
    show_user_controls_bar()

    st.divider()

    # Mostrar información del usuario
    st.subheader("📋 Información de tu Cuenta")

    user_credits = db_manager.get_user_credits(current_user['email'])

    st.markdown(f"""
    <div class="user-info-display">
        <strong>👤 Usuario:</strong> {current_user['full_name']}<br>
        <small>{current_user['email']}</small><br>
        <strong> 🪙 Créditos disponibles: {user_credits}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Mostrar reservas existentes del usuario (solo lectura)
    user_today_reservations = db_manager.get_user_reservations_for_date(current_user['email'], today)
    user_tomorrow_reservations = db_manager.get_user_reservations_for_date(current_user['email'], tomorrow)

    st.subheader("📅 Tus Reservas Actuales")

    if user_today_reservations or user_tomorrow_reservations:
        if user_today_reservations:
            st.write(f"**Hoy ({format_date_short(today)}):** {len(user_today_reservations)} hora(s)")
            for hour in sorted(user_today_reservations):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")

        if user_tomorrow_reservations:
            st.write(f"**Mañana ({format_date_short(tomorrow)}):** {len(user_tomorrow_reservations)} hora(s)")
            for hour in sorted(user_tomorrow_reservations):
                st.write(f"  • {format_hour(hour)} - {format_hour(hour + 1)}")
    else:
        st.info("No tienes reservas programadas")

        # PARTE NUEVA: Cómo Reservar (igual que en vista normal)
        st.markdown("### Cómo Reservar")
        st.write("1. Revisa que estés en **los horarios de reserva** y que tengas **créditos disponibles!**")
        st.write("2. **Selecciona los horarios disponibles** que desees entre hoy y mañana (hasta 2 horas por día)")
        st.write("3. **Confirma tu reserva** con un click")
        st.write("4. Te llegará una **confirmación a tu correo registrado**")

        # PARTE NUEVA: Mostrar reglas de reserva
        with st.expander("📋 Reglas de Reserva"):
            is_vip = db_manager.is_vip_user(current_user['email'])
            horario_reservas = "8:00 AM - 8:00 PM" if is_vip else "8:00 AM - 5:00 PM"
            tipo_usuario = " (Usuario VIP)" if is_vip else ""

            st.markdown(f"""
            • **Solo se puede hacer reservar para hoy y para mañana**<br>
            • **Máximo 2 horas** por persona por día<br>
            • **Horas consecutivas** requeridas si se reservan 2 horas<br>
            • No se permite reservar la cancha en **los mismos horarios dos días consecutivos**<br>
            • **Horario para hacer reservas:** {horario_reservas}<br>
            • **Horario de cancha:** 6:00 AM - 9:00 PM<br>
            • ⏰ **Importante:** Solo puedes hacer reservas dentro del horario permitido
            """, unsafe_allow_html=True)

        # Mostrar info créditos
        with st.expander("💰 ¿Cómo Adquirir Créditos?"):
            st.markdown("""
            **💳 Costo de Créditos:**  
            • Cada crédito = 1 hora de cancha  
            • Precio por crédito: **$15.000 COP**

            **📞 Contacto para Recargar:**

            **Orlando**  
            **WhatsApp:** [3193368749](https://wa.me/573193368749)

            **⏰ Horarios de Atención:**  
            • **Lunes a Sábado:** 9:00 AM - 11:00 AM  
            • **Domingos y Festivos:** 5:00 PM - 7:00 PM

            **💡 Recomendaciones:**  
            • Planifica tu recarga con anticipación para evitar quedarte sin créditos  
            • Contacta únicamente en los horarios establecidos para una respuesta rápida  
            • Puedes recargar múltiples créditos en una sola transacción
            """)


    # Mostrar calendario en modo de solo lectura
    st.subheader("👁️ Vista de Disponibilidad (Solo Lectura)")

    # Obtener datos de reservas para mostrar
    today_reservations = db_manager.get_reservations_with_names_for_date(today)
    tomorrow_reservations = db_manager.get_reservations_with_names_for_date(tomorrow)

    today_col, tomorrow_col = st.columns(2)

    with today_col:
        st.markdown(f"""
        <div class="calendar-header">
            {format_date_short(today)}<br>
            <small>HOY</small>
        </div>
        """, unsafe_allow_html=True)

        show_read_only_day_schedule(today, today_reservations, current_user)

    with tomorrow_col:
        st.markdown(f"""
        <div class="calendar-header">
            {format_date_short(tomorrow)}<br>
            <small>MAÑANA</small>
        </div>
        """, unsafe_allow_html=True)

        show_read_only_day_schedule(tomorrow, tomorrow_reservations, current_user)

def show_read_only_day_schedule(date, reservations_dict, current_user):
    """Mostrar horarios en modo de solo lectura"""
    user_reservations = db_manager.get_user_reservations_for_date(current_user['email'], date)

    for hour in COURT_HOURS:
        is_reserved = hour in reservations_dict
        is_my_reservation = hour in user_reservations

        if is_my_reservation:
            # Mis reservas
            st.markdown(f"""
            <div class="time-slot-my-reservation">
                {format_hour(hour)}<br>Tu Reserva
            </div>
            """, unsafe_allow_html=True)
        elif is_reserved:
            # Reserva de otro usuario
            reserved_name = reservations_dict[hour]
            if len(reserved_name) > 12:
                displayed_name = reserved_name[:9] + "..."
            else:
                displayed_name = reserved_name

            st.markdown(f"""
            <div class="time-slot-reserved">
                {format_hour(hour)}<br>{displayed_name}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Disponible (pero no seleccionable)
            st.markdown(f"""
            <div style="
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                color: #6c757d;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                margin: 5px 0;
                opacity: 0.7;
            ">
                {format_hour(hour)}<br>Disponible
            </div>
            """, unsafe_allow_html=True)

def show_reservation_tab():
    """Mostrar la pestaña de reservas con caché optimizado"""
    apply_custom_css()

    # Initialize reservation workflow state
    if "reservation_confirmed" not in st.session_state:
        st.session_state.reservation_confirmed = False

    # Obtener información del usuario actual
    current_user = get_current_user()

    if not current_user:
        st.error("Error de autenticación. Por favor actualiza la página.")
        return

    # Verificar si puede hacer reservas en este momento
    can_reserve_now, reservation_time_error = db_manager.can_user_make_reservation_now(current_user['email'])

    if not can_reserve_now:
        # Mostrar mensaje de horario restringido
        is_vip = db_manager.is_vip_user(current_user['email'])
        horario_permitido = "8:00 AM a 8:00 PM" if is_vip else "8:00 AM a 5:00 PM"
        tipo_usuario = "VIP " if is_vip else ""

        st.error(f"🕐 {reservation_time_error}")
        st.info(f"💡 Como usuario {tipo_usuario}puedes hacer reservas de {horario_permitido}")

        # Mostrar información pero deshabilitar funcionalidad
        show_read_only_schedule_view(current_user)
        return


    today, tomorrow = get_today_tomorrow()
    current_hour = get_current_hour()

    # CACHING SYSTEM - Cache data for 30 seconds
    cache_key = f"reservations_cache_{today}_{tomorrow}"
    cache_timestamp_key = f"cache_timestamp_{today}_{tomorrow}"

    # Check if we need to refresh cache (every 30 seconds)
    current_time = time.time()
    should_refresh = (
            cache_key not in st.session_state or
            cache_timestamp_key not in st.session_state or
            current_time - st.session_state[cache_timestamp_key] > 30
    )

    if should_refresh:
        with st.spinner("Actualizando disponibilidad..."):
            # Single database call instead of 4 separate calls
            summary = db_manager.get_date_reservations_summary([today, tomorrow], current_user['email'])

            today_str = today.strftime('%Y-%m-%d')
            tomorrow_str = tomorrow.strftime('%Y-%m-%d')

            today_reservations = summary['reservation_names'].get(today_str, {})
            tomorrow_reservations = summary['reservation_names'].get(tomorrow_str, {})
            user_today_reservations = summary['user_reservations'].get(today_str, [])
            user_tomorrow_reservations = summary['user_reservations'].get(tomorrow_str, [])

        # Cache the data (same structure as before)
        st.session_state[cache_key] = {
            'today_reservations': today_reservations,
            'tomorrow_reservations': tomorrow_reservations,
            'user_today_reservations': user_today_reservations,
            'user_tomorrow_reservations': user_tomorrow_reservations
        }
        st.session_state[cache_timestamp_key] = current_time

        # Show cache refresh indicator
        #st.success("✅ Datos actualizados", icon="🔄")

    else:
        # Use cached data (fast)
        cached_data = st.session_state[cache_key]
        today_reservations = cached_data['today_reservations']
        tomorrow_reservations = cached_data['tomorrow_reservations']
        user_today_reservations = cached_data['user_today_reservations']
        user_tomorrow_reservations = cached_data['user_tomorrow_reservations']

    # Show cache age info (optional - for debugging)
    cache_age = get_cache_age()
    if cache_age < 30:
        st.caption(f"🕐 Datos actualizados hace {int(cache_age)}s")

    # Mostrar barra de controles
    show_user_controls_bar()

    st.divider()

    st.markdown(" ")

    # Rest of the layout code remains the same
    use_desktop_layout = st.checkbox("🖥️ Usar vista desktop", key="desktop_layout",
                                     help="Activa para pantallas grandes")

    if use_desktop_layout:
        # Layout desktop
        left_col, right_col = st.columns([1, 2])

        with left_col:
            show_reservation_details(today, tomorrow, current_user, user_today_reservations, user_tomorrow_reservations)

        with right_col:
            show_calendar_view(today, tomorrow, today_reservations, tomorrow_reservations, current_hour, current_user)
    else:
        # Layout móvil (default)
        show_mobile_layout(today, tomorrow, today_reservations, tomorrow_reservations, current_hour, current_user,
                           user_today_reservations, user_tomorrow_reservations)


def show_reservation_success_message():
    """Mostrar mensaje de éxito de reserva con datos específicos"""
    if not st.session_state.get('last_reservation_data'):
        return

    data = st.session_state.last_reservation_data
    remaining_credits = db_manager.get_user_credits(st.session_state.user_info['email'])

    sorted_hours = sorted(data['hours'])
    start_time = format_hour(min(sorted_hours))
    end_time = format_hour(max(sorted_hours) + 1)

    st.markdown(f"""
    <div class="success-message">
        <h3>✅ ¡Reserva Confirmada!</h3>
        <p><strong>Nombre:</strong> {data['name']}</p>
        <p><strong>Fecha:</strong> {format_date_full(data['date'])}</p>
        <p><strong>Hora:</strong> {start_time} - {end_time}</p>
        <p><strong>Duración:</strong> {len(sorted_hours)} hora(s)</p>
        <p><strong>💰 Créditos usados:</strong> {data['credits_used']}</p>
        <p><strong>💳 Créditos restantes:</strong> {remaining_credits}</p>
        <p>📧 <em>Email de confirmación enviado</em></p>
    </div>
    """, unsafe_allow_html=True)

    # Limpiar los datos después de mostrar
    if 'last_reservation_data' in st.session_state:
        del st.session_state['last_reservation_data']

def show_mobile_layout(today, tomorrow, today_reservations, tomorrow_reservations, current_hour, current_user,
                       user_today_reservations, user_tomorrow_reservations):
    """Mostrar layout móvil optimizado"""

    # PARTE 1: Información del usuario y reservas existentes (ARRIBA)
    st.subheader("Detalles de la Reserva")

    user_credits = db_manager.get_user_credits(current_user['email'])

    # Mostrar información del usuario
    st.markdown(f"""
    <div class="user-info-display">
        <strong>👤 Reservando como:</strong><br>
        {current_user['full_name']}<br>
        <small>{current_user['email']}</small> <br>
        <strong> 🪙 Créditos disponibles: {user_credits}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Mostrar reservas existentes del usuario
    show_user_existing_reservations(today, tomorrow, user_today_reservations, user_tomorrow_reservations)

    # PARTE 2: Cómo Reservar (DESPUÉS DE RESERVAS ACTUALES)
    st.markdown("### Cómo Reservar")
    st.write("1. Revisa que estés en **los horarios de reserva** y que tengas **créditos disponibles!**")
    st.write("2. **Selecciona los horarios disponibles** que desees entre hoy y mañana (hasta 2 horas por día)")
    st.write("3. **Confirma tu reserva** con un click")
    st.write("4. Te llegará una **confirmación a tu correo registrado**")

    # Mostrar reglas de reserva
    with st.expander("📋 Reglas de Reserva"):
        is_vip = db_manager.is_vip_user(current_user['email'])
        horario_reservas = "8:00 AM - 8:00 PM" if is_vip else "8:00 AM - 5:00 PM"

        st.markdown(f"""
        • **Solo se puede hacer reservar para hoy y para mañana**<br>
        • **Máximo 2 horas** por persona por día<br>
        • **Horas consecutivas** requeridas si se reservan 2 horas<br>
        • No se permite reservar la cancha en **los mismos horarios dos días consecutivos**<br>
        • **Horario para hacer reservas:** {horario_reservas}<br>
        • **Horario de cancha:** 6:00 AM - 9:00 PM<br>
        • ⏰ **Importante:** Solo puedes hacer reservas dentro del horario permitido
        """, unsafe_allow_html=True)

    # Mostrar info créditos
    with st.expander("💰 ¿Cómo Adquirir Créditos?"):
        st.markdown("""
        **💳 Costo de Créditos:**  
        • Cada crédito = 1 hora de cancha  
        • Precio por crédito: **$15.000 COP**

        **📞 Contacto para Recargar:**

        **Orlando**  
        **WhatsApp:** [3193368749](https://wa.me/573193368749)

        **⏰ Horarios de Atención:**  
        • **Lunes a Sábado:** 9:00 AM - 11:00 AM  
        • **Domingos y Festivos:** 5:00 PM - 7:00 PM

        **💡 Recomendaciones:**  
        • Planifica tu recarga con anticipación para evitar quedarte sin créditos  
        • Contacta únicamente en los horarios establecidos para una respuesta rápida  
        • Puedes recargar múltiples créditos en una sola transacción
        """)

    # PARTE 3: Vista de calendario (MEDIO)
    show_calendar_view(today, tomorrow, today_reservations, tomorrow_reservations, current_hour, current_user)

    # Mostrar mensaje de éxito debajo del calendario
    if st.session_state.get('reservation_confirmed', False):
        show_reservation_success_message()
        st.session_state.reservation_confirmed = False

        # PARTE 4: SOLO Confirmación de reserva (ABAJO DEL CALENDARIO)
    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)

    if selected_hours and selected_date is not None:
        st.markdown("### Confirmar Reserva")

        st.write(f"**Fecha:** {format_date_full(selected_date)}")
        st.write(f"**Slots de Tiempo:** {len(selected_hours)} hora(s)")

        for hour in sorted(selected_hours):
            st.write(f"• {format_hour(hour)} - {format_hour(hour + 1)}")

        if len(selected_hours) > 1:
            start_time = format_hour(min(selected_hours))
            end_time = format_hour(max(selected_hours) + 1)
            st.write(f"**Tiempo Total:** {start_time} - {end_time}")

        # Mostrar resumen de la reserva
        st.info(f"Reservando para: **{current_user['full_name']}** ({current_user['email']})")

        # Add visual emphasis and bigger button
        st.markdown('<div class="big-confirm-button">', unsafe_allow_html=True)
        st.button(
            r"$\textsf{\normalsize  ✅ Confirmar Reserva}$",
            type="primary",
            use_container_width=True,
            key="mobile_big_confirm_btn",
            on_click=confirm_reservation_callback,
            args=(current_user, selected_date, selected_hours)
        )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("Selecciona los horarios disponibles en el calendario para continuar")

def show_reservation_details(today_date, tomorrow_date, current_user, user_today_reservations, user_tomorrow_reservations):
    """Mostrar panel de detalles de reserva"""

    if st.session_state.get('mobile_layout', False):
        return

    st.subheader("Detalles de la Reserva")

    # Mostrar información de los créditos del usuario
    user_credits = db_manager.get_user_credits(current_user['email'])

    # Mostrar información del usuario
    st.markdown(f"""
    <div class="user-info-display">
        <strong>👤 Reservando como:</strong><br>
        {current_user['full_name']}<br>
        <small>{current_user['email']}</small> <br>
        <strong> 🪙 Créditos disponibles: {user_credits}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Mostrar reservas existentes del usuario
    show_user_existing_reservations(today_date, tomorrow_date, user_today_reservations, user_tomorrow_reservations)

    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)

    # Mostrar reglas de reserva
    with st.expander("📋 Reglas de Reserva"):
        is_vip = db_manager.is_vip_user(current_user['email'])
        horario_reservas = "8:00 AM - 8:00 PM" if is_vip else "8:00 AM - 5:00 PM"

        st.markdown(f"""
        • **Solo se puede hacer reservar para hoy y para mañana**<br>
        • **Máximo 2 horas** por persona por día<br>
        • **Horas consecutivas** requeridas si se reservan 2 horas<br>
        • No se permite reservar la cancha en **los mismos horarios dos días consecutivos**<br>
        • **Horario para hacer reservas:** {horario_reservas}<br>
        • **Horario de cancha:** 6:00 AM - 9:00 PM<br>
        • ⏰ **Importante:** Solo puedes hacer reservas dentro del horario permitido
        """, unsafe_allow_html=True)

    # Mostrar info créditos
    with st.expander("💰 ¿Cómo Adquirir Créditos?"):
        st.markdown("""
        **💳 Costo de Créditos:**  
        • Cada crédito = 1 hora de cancha  
        • Precio por crédito: **$15.000 COP**

        **📞 Contacto para Recargar:**

        **Orlando**  
        **WhatsApp:** [3193368749](https://wa.me/573193368749)

        **⏰ Horarios de Atención:**  
        • **Lunes a Sábado:** 9:00 AM - 11:00 AM  
        • **Domingos y Festivos:** 5:00 PM - 7:00 PM

        **💡 Recomendaciones:**  
        • Planifica tu recarga con anticipación para evitar quedarte sin créditos  
        • Contacta únicamente en los horarios establecidos para una respuesta rápida  
        • Puedes recargar múltiples créditos en una sola transacción
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


        # Formulario simplificado (sin nombre y email)
        st.markdown("### Confirmar Reserva")

        # Mostrar resumen de la reserva
        st.info(f"Reservando para: **{current_user['full_name']}** ({current_user['email']})")

        # Add visual emphasis and bigger button
        st.markdown('<div class="big-confirm-button">', unsafe_allow_html=True)
        st.button(
            r"$\textsf{\normalsize  ✅ Confirmar Reserva}$",
            type="primary",
            use_container_width=True,
            key="big_confirm_btn",
            on_click=confirm_reservation_callback,
            args=(current_user, selected_date, selected_hours)
        )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("Selecciona los horarios disponibles en el calendario para continuar")

        st.markdown("### Cómo Reservar")
        st.write("1. Revisa que estés en **los horarios de reserva** y que tengas **créditos disponibles!**")
        st.write("2. **Selecciona los horarios disponibles** que desees entre hoy y mañana (hasta 2 horas por día)")
        st.write("3. **Confirma tu reserva** con un click")
        st.write("4. Te llegará una **confirmación a tu correo registrado**")

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

def confirm_reservation_callback(current_user, selected_date, selected_hours):
    """Callback for reservation confirmation"""
    success = handle_reservation_submission(current_user, selected_date, selected_hours)
    if success:
        st.session_state.reservation_confirmed = True


def handle_reservation_submission(current_user, date, selected_hours):
    """Handle reservation submission with transaction safety"""

    # ... existing validation code stays the same ...

    # TRANSACTION-SAFE RESERVATION CREATION
    successful_reservations = []
    failed_hours = []

    with st.spinner("Processing reservation with transaction safety..."):
        for hour in selected_hours:
            try:
                # Start individual reservation transaction
                reservation_success = create_reservation_with_transaction(
                    current_user, date, hour
                )

                if reservation_success:
                    successful_reservations.append(hour)
                    print(f"✅ Reserved hour {hour} successfully")
                else:
                    failed_hours.append(hour)
                    print(f"❌ Failed to reserve hour {hour}")

            except Exception as e:
                print(f"❌ Exception reserving hour {hour}: {e}")
                failed_hours.append(hour)

    # Handle results
    if len(successful_reservations) == len(selected_hours):
        # Complete success - NO mostrar mensaje aquí, solo marcar el flag
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
        return True

    elif len(successful_reservations) > 0:
        # Partial success
        st.warning(
            f"✅ Reserved {len(successful_reservations)} hour(s). "
            f"❌ Failed: {len(failed_hours)} hour(s) (already taken or error)"
        )

        # Update selection to only failed hours
        st.session_state.selected_hours = failed_hours
        invalidate_reservation_cache()
        return False

    else:
        # Complete failure
        st.error("❌ No reservations could be made. All selected hours are unavailable.")
        st.session_state.selected_hours = []
        st.session_state.selected_date = None
        invalidate_reservation_cache()
        return False


def create_reservation_with_transaction(current_user, date, hour):
    """Create a single reservation with atomic transaction"""
    try:
        # Check availability one more time
        if not db_manager.is_hour_available(date, hour):
            return False

        # Check user has credits
        user_credits = db_manager.get_user_credits(current_user['email'])
        if user_credits < 1:
            return False

        # ATOMIC TRANSACTION: Both reservation and credit deduction must succeed

        # Step 1: Create reservation
        reservation_success = db_manager.save_reservation(
            date, hour, current_user['full_name'], current_user['email']
        )

        if not reservation_success:
            return False

        # Step 2: Deduct credit
        credit_success = db_manager.use_credits_for_reservation(
            current_user['email'], 1, date.strftime('%Y-%m-%d'), hour
        )

        if not credit_success:
            # ROLLBACK: Delete the reservation we just created
            rollback_success = db_manager.delete_reservation(date.strftime('%Y-%m-%d'), hour)
            if rollback_success:
                print(f"🔄 Rollback successful for hour {hour}")
            else:
                print(f"❌ CRITICAL: Failed to rollback reservation for hour {hour}")
            return False

        return True

    except Exception as e:
        print(f"❌ Transaction error for hour {hour}: {e}")
        return False

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

def show_success_message_with_credits(name, date_obj, selected_hours, credits_used):
    """Mostrar mensaje de éxito con información de créditos"""
    sorted_hours = sorted(selected_hours)
    start_time = format_hour(min(sorted_hours))
    end_time = format_hour(max(sorted_hours) + 1)

    remaining_credits = db_manager.get_user_credits(st.session_state.user_info['email'])

    st.markdown(f"""
    <div class="success-message">
        <h3>✅ ¡Reserva Confirmada!</h3>
        <p><strong>Nombre:</strong> {name}</p>
        <p><strong>Fecha:</strong> {format_date_full(date_obj)}</p>
        <p><strong>Hora:</strong> {start_time} - {end_time}</p>
        <p><strong>Duración:</strong> {len(sorted_hours)} hora(s)</p>
        <p><strong>💰 Créditos usados:</strong> {credits_used}</p>
        <p><strong>💳 Créditos restantes:</strong> {remaining_credits}</p>
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

        # Un slot es seleccionable si no está reservado y no es pasado
        is_selectable = not is_reserved and not is_past_hour

        # Determinar el estado del botón
        if is_my_reservation:
            # Es una reserva del usuario actual
            button_text = f"{format_hour(hour)}\nTu Reserva"
            disabled = True
            st.markdown(f"""
                <div class="time-slot-my-reservation">
                    {button_text}
                </div>
                """, unsafe_allow_html=True)
            continue
        elif is_reserved:
            # Obtener el nombre del usuario que reservó
            reserved_name = reservations_dict[hour]
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
    """Manejar clic en un slot de tiempo usando datos cacheados"""

    selected_hours = st.session_state.get('selected_hours', [])
    selected_date = st.session_state.get('selected_date', None)

    # Get user existing hours from cached data (NO DATABASE CALL)
    today, tomorrow = get_today_tomorrow()
    cache_key = f"reservations_cache_{today}_{tomorrow}"

    if cache_key in st.session_state:
        cached_data = st.session_state[cache_key]
        if date == today:
            user_existing_hours = cached_data['user_today_reservations']
        else:
            user_existing_hours = cached_data['user_tomorrow_reservations']
    else:
        # Fallback if no cache (shouldn't happen) - use optimized method
        summary = db_manager.get_date_reservations_summary([date], current_user['email'])
        date_str = date.strftime('%Y-%m-%d')
        user_existing_hours = summary['user_reservations'].get(date_str, [])

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

        # Validar si las horas son consecutivas con el día anterior
        if validate_consecutive_days_conflict(hour, date, current_user):
            return

        # Seleccionar (verificar límites)
        if len(selected_hours) >= 2:
            st.error("Máximo 2 horas por selección")
            return

        # Verificar créditos antes de seleccionar
        credits_needed = len(selected_hours) + 1  # +1 porque vamos a agregar esta hora
        user_credits = db_manager.get_user_credits(current_user['email'])

        if user_credits < credits_needed:
            st.error(f"❌ Créditos insuficientes. Necesitas {credits_needed} créditos, tienes {user_credits}.")
            st.info("💡 Contacta al administrador para recargar créditos.")
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

def validate_consecutive_days_conflict(hour, date, current_user):
    """Validate that user doesn't reserve same time slot on consecutive days"""
    today, tomorrow = get_today_tomorrow()

    # Get cached data to avoid database calls
    cache_key = f"reservations_cache_{today}_{tomorrow}"

    if cache_key in st.session_state:
        cached_data = st.session_state[cache_key]
        user_today_reservations = cached_data['user_today_reservations']
        user_tomorrow_reservations = cached_data['user_tomorrow_reservations']
    else:
        # Fallback if no cache
        summary = db_manager.get_date_reservations_summary([today, tomorrow], current_user['email'])
        today_str = today.strftime('%Y-%m-%d')
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        user_today_reservations = summary['user_reservations'].get(today_str, [])
        user_tomorrow_reservations = summary['user_reservations'].get(tomorrow_str, [])

    # Check if trying to book same hour on consecutive days
    if date == today and hour in user_tomorrow_reservations:
        st.error(
            f"No puedes reservar a las {format_hour(hour)} hoy porque ya lo tienes reservado mañana. No se permite reservar el mismo horario dos días seguidos.")
        return True
    elif date == tomorrow and hour in user_today_reservations:
        st.error(
            f"No puedes reservar a las {format_hour(hour)} mañana porque ya lo tienes reservado hoy. No se permite reservar el mismo horario dos días seguidos.")
        return True

    return False

def init_reservation_session_state():
    """Inicializar estado de sesión para reservas"""
    if 'selected_hours' not in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None

def invalidate_reservation_cache():
    """Force cache refresh"""
    today, tomorrow = get_today_tomorrow()
    cache_key = f"reservations_cache_{today}_{tomorrow}"
    cache_timestamp_key = f"cache_timestamp_{today}_{tomorrow}"

    if cache_key in st.session_state:
        del st.session_state[cache_key]
    if cache_timestamp_key in st.session_state:
        del st.session_state[cache_timestamp_key]

def get_cache_age():
    """Get age of current cache in seconds"""
    today, tomorrow = get_today_tomorrow()
    cache_timestamp_key = f"cache_timestamp_{today}_{tomorrow}"

    if cache_timestamp_key in st.session_state:
        return time.time() - st.session_state[cache_timestamp_key]
    return float('inf')