"""
Aplicación de Administración para Sistema de Reservas de Cancha de Tenis
Gestión de reservas, usuarios y créditos
"""

import streamlit as st
from admin_auth import admin_auth_manager, require_admin_auth
from admin_database import admin_db_manager
from timezone_utils import get_colombia_now, get_colombia_today
from email_config import email_manager
import pandas as pd


# Colores US Open
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"


def setup_admin_page_config():
    """Configurar la página de administración"""
    st.set_page_config(
        page_title="Admin - Reservas Tenis",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_admin_styles():
    """Aplicar estilos CSS para la interfaz de administración"""
    st.markdown(f"""
    <style>
    .admin-header {{
        background: linear-gradient(135deg, {US_OPEN_BLUE} 0%, {US_OPEN_LIGHT_BLUE} 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }}

    .stat-card {{
        background: white;
        border: 2px solid {US_OPEN_LIGHT_BLUE};
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}

    .stat-number {{
        font-size: 2rem;
        font-weight: bold;
        color: {US_OPEN_BLUE};
    }}

    .stat-label {{
        color: #666;
        font-size: 0.9rem;
        margin-top: 5px;
    }}

    .success-card {{
        background: #e8f5e8;
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: #2e7d32;
    }}

    .warning-card {{
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: #856404;
    }}

    .error-card {{
        background: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: #721c24;
    }}

    /* Segmented control styling */
    .stSegmentedControl > div {{
        background-color: white;
        border-radius: 8px;
        border: 2px solid {US_OPEN_LIGHT_BLUE};
        margin: 10px 0;
    }}

    .stSegmentedControl button {{
        color: {US_OPEN_BLUE} !important;
        font-weight: 500 !important;
    }}

    .stSegmentedControl button[aria-selected="true"] {{
        background-color: {US_OPEN_LIGHT_BLUE} !important;
        color: white !important;
        font-weight: bold !important;
    }}
    
    /* Mejorar estilo de expanders */
    .streamlit-expanderHeader {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }}
    
    .streamlit-expanderContent {{
        padding: 12px 16px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def show_admin_login():
    """Mostrar interfaz de login de administrador"""
    st.markdown("""
    <div class="admin-header">
        <h1>🔐 Acceso de Administrador</h1>
        <p>Sistema de Gestión de Reservas de Cancha de Tenis</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("admin_login_form"):
            st.markdown("### 👤 Iniciar Sesión")

            username = st.text_input(
                "Usuario",
                placeholder="Ingresa tu usuario administrativo"
            )

            password = st.text_input(
                "Contraseña",
                type="password",
                placeholder="Ingresa tu contraseña"
            )

            login_button = st.form_submit_button(
                "Iniciar Sesión",
                type="primary",
                use_container_width=True
            )

            if login_button:
                if admin_auth_manager.login_admin(username, password):
                    st.success("✅ Acceso concedido")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

def show_admin_dashboard():
    """Mostrar el panel principal de administración"""
    admin_user = st.session_state.get('admin_user')

    # Header con información del admin
    st.markdown(f"""
    <div class="admin-header">
        <h1>⚙️ Panel de Administración</h1>
        <p>Bienvenido, {admin_user['full_name']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Barra superior mejorada
    st.markdown("""
    <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; margin: 15px 0; 
                backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="color: white; opacity: 0.9;">
                <i class="fas fa-clock"></i> <span style="font-size: 14px;">Última actualización: {}</span>
            </div>
        </div>
    </div>
    """.format(get_colombia_now().strftime('%d/%m/%Y %H:%M:%S')), unsafe_allow_html=True)

    # Controles de acción
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col2:
        if st.button("🔄 Actualizar", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Datos actualizados")
            st.rerun()

    with col3:
        if st.button("📊 Exportar", type="secondary", use_container_width=True):
            with st.spinner("📊 Generando archivo Excel..."):
                try:
                    # Obtener datos
                    users_data = admin_db_manager.get_all_users_for_export()
                    reservations_data = admin_db_manager.get_all_reservations_for_export()
                    credits_data = admin_db_manager.get_credit_transactions_for_export()

                    # Crear archivo Excel
                    from io import BytesIO

                    # Crear buffer en memoria
                    buffer = BytesIO()

                    # Crear archivo Excel con múltiples hojas
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        # Hoja de usuarios
                        if users_data:
                            df_users = pd.DataFrame(users_data)
                            df_users.to_excel(writer, sheet_name='Usuarios', index=False)

                        # Hoja de reservas
                        if reservations_data:
                            df_reservations = pd.DataFrame(reservations_data)
                            df_reservations.to_excel(writer, sheet_name='Reservas', index=False)

                        # Hoja de créditos
                        if credits_data:
                            df_credits = pd.DataFrame(credits_data)
                            df_credits.to_excel(writer, sheet_name='Créditos', index=False)

                    buffer.seek(0)

                    # Generar nombre de archivo con fecha
                    fecha_actual = get_colombia_now().strftime('%Y%m%d_%H%M%S')
                    filename = f"reservas_tenis_export_{fecha_actual}.xlsx"

                    # Botón de descarga
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=buffer.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )

                    st.success(
                        f"✅ Archivo generado: {len(users_data)} usuarios, {len(reservations_data)} reservas, {len(credits_data)} transacciones")

                except Exception as e:
                    st.error(f"❌ Error generando archivo: {str(e)}")

    with col4:
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
            admin_auth_manager.logout_admin()
            st.rerun()

    st.divider()


    # Control de navegación segmentado
    previous_tab = st.session_state.get('admin_current_tab', "📊 Dashboard")

    tab = st.segmented_control(
        "Navegación Admin",
        ["📊 Dashboard", "📅 Reservas", "👥 Usuarios", "💰 Créditos", "🔧 Mantenimiento", "⚙️ Config"],  # AGREGADO
        selection_mode="single",
        default="📊 Dashboard",
        label_visibility="collapsed",
    )

    # Limpiar búsquedas si cambió de pestaña
    if tab != previous_tab:
        # Limpiar estados de búsqueda
        if 'selected_user_for_reservations' in st.session_state:
            del st.session_state.selected_user_for_reservations
        if 'found_users' in st.session_state:
            del st.session_state.found_users

        # Guardar pestaña actual
        st.session_state.admin_current_tab = tab

    # Mostrar sección correspondiente
    if tab == "📊 Dashboard":
        show_dashboard_tab()
    elif tab == "📅 Reservas":
        show_reservations_management_tab()
    elif tab == "👥 Usuarios":
        show_users_management_tab()
    elif tab == "💰 Créditos":
        show_credits_management_tab()
    elif tab == "🔧 Mantenimiento":  # NUEVO
        show_maintenance_tab()
    elif tab == "⚙️ Config":
        show_config_tab()

def show_dashboard_tab():
    """Mostrar estadísticas y dashboard"""
    st.subheader("📊 Dashboard & Estadísticas")

    # Obtener estadísticas
    stats = admin_db_manager.get_system_statistics()

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_users']}</div>
            <div class="stat-label">Usuarios Registrados</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['active_users']}</div>
            <div class="stat-label">Usuarios Activos</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['today_reservations']}</div>
            <div class="stat-label">Reservas Hoy</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_credits_issued']}</div>
            <div class="stat-label">Créditos Emitidos</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Gráficos y estadísticas detalladas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Distribución por Día de la Semana")
        day_stats = admin_db_manager.get_reservations_by_day_of_week()

        if day_stats['counts'] and sum(day_stats['counts']) > 0:
            import plotly.graph_objects as go

            fig = go.Figure(data=[go.Pie(
                labels=day_stats['days'],
                values=day_stats['counts'],
                hole=0.4,
                textinfo='label+percent',
                textposition='inside',
                hovertemplate='<b>%{label}</b><br>%{value} reservas<br>%{percent}<extra></extra>',
                marker=dict(colors=['#001854', '#2478CC', '#FFD400', '#FF6B6B', '#4ECDC4', '#95E1D3', '#F38181'])
            )])

            fig.update_layout(
                showlegend=False,
                height=400,
                margin=dict(t=0, b=0, l=0, r=0)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de reservas disponibles")

    with col2:
        import pandas as pd
        st.subheader("⏰ Horas Más Populares")
        hourly_stats = admin_db_manager.get_hourly_reservation_stats()
        if hourly_stats:
            df_hourly = pd.DataFrame(hourly_stats)
            st.bar_chart(df_hourly.set_index('hour')['count'])
        else:
            st.info("No hay datos de horarios disponibles")

    st.divider()

    # Estadísticas de usuarios
    st.subheader("🏆 Usuarios Más Activos")
    user_stats = admin_db_manager.get_user_reservation_statistics()
    if user_stats:
        for i, user in enumerate(user_stats[:5], 1):
            # Crear expander con título más prominente y ancho completo
            expander_title = f"**{i}. {user['name']}** • {user['reservations']} reservas"

            with st.expander(expander_title, expanded=False):
                # Obtener datos detallados del usuario
                user_detail = admin_db_manager.search_users_detailed(user['email'])
                if user_detail:
                    user_info = user_detail[0]

                    # Card con información organizada
                    st.markdown(f"""
                    <div style="
                        background: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 16px;
                        margin: 8px 0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                            <div>
                                <p style="margin: 4px 0;"><strong>📧 Email:</strong> {user_info['email']}</p>
                                <p style="margin: 4px 0;"><strong>🎯 Estado:</strong> {'✅ Activo' if user_info['is_active'] else '❌ Inactivo'}</p>
                                <p style="margin: 4px 0;"><strong>💰 Créditos:</strong> {user_info.get('credits', 0)}</p>
                            </div>
                            <div>
                                <p style="margin: 4px 0;"><strong>🕒 Último login:</strong> {user_info['last_login'][:10] if user_info.get('last_login') else 'Nunca'}</p>
                                <p style="margin: 4px 0;"><strong>📅 Registrado:</strong> {user_info['created_at'][:10]}</p>
                                <p style="margin: 4px 0;"><strong>🎾 Total reservas:</strong> {user['reservations']}</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ No se pudieron cargar los detalles del usuario")
    else:
        st.info("📊 No hay datos de usuarios disponibles")

    st.divider()

    # NUEVA SECCIÓN: Vista de Calendario Semanal
    st.subheader("📅 Calendario de Reservas Semanal")

    # Controles de navegación
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    # Inicializar week_offset si no existe
    if 'calendar_week_offset' not in st.session_state:
        st.session_state.calendar_week_offset = 0

    with col1:
        if st.button("⬅️ Anterior", key="prev_week"):
            st.session_state.calendar_week_offset -= 1
            st.rerun()

    with col2:
        if st.button("➡️ Siguiente", key="next_week"):
            st.session_state.calendar_week_offset += 1
            st.rerun()

    with col3:
        if st.button("📍 Semana Actual", key="current_week"):
            st.session_state.calendar_week_offset = 0
            st.rerun()

    with col4:
        if st.button("🔄 Actualizar", key="refresh_calendar"):
            st.cache_data.clear()
            st.success("✅ Calendario actualizado")

    # Obtener datos del calendario
    calendar_data = admin_db_manager.get_weekly_calendar_data(st.session_state.calendar_week_offset)

    if calendar_data['week_dates']:
        # Mostrar información de la semana
        week_info = f"📊 Semana del {calendar_data['week_start']} al {calendar_data['week_end']} • {calendar_data['total_reservations']} reservas"
        st.info(week_info)

        # Crear el calendario como tabla
        week_dates = calendar_data['week_dates']
        reservations_grid = calendar_data['reservations_grid']

        # Nombres de los días
        day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        # Horarios de la cancha (6 AM a 9 PM)
        court_hours = list(range(6, 22))

        # Crear DataFrame para el calendario
        import pandas as pd

        # Preparar datos para la tabla
        calendar_table = []

        for hour in court_hours:
            row = {'Hora': f"{hour:02d}:00"}

            for i, date in enumerate(week_dates):
                date_str = date.strftime('%Y-%m-%d')
                day_name = day_names[i]

                # Obtener reserva para este día/hora
                reservation = reservations_grid.get(date_str, {}).get(hour)

                if reservation:
                    # Mostrar nombre (truncado si es muy largo)
                    name = reservation['name']
                    if len(name) > 12:
                        name = name[:9] + "..."
                    row[f"{day_name}\n{date.strftime('%d/%m')}"] = f"🎾 {name}"
                else:
                    row[f"{day_name}\n{date.strftime('%d/%m')}"] = "⚪ Libre"

            calendar_table.append(row)

        # Crear DataFrame
        df_calendar = pd.DataFrame(calendar_table)

        # Mostrar la tabla con estilo
        st.markdown("### 📋 Vista de Calendario")

        # Aplicar estilos a la tabla
        def style_calendar_table(val):
            """Aplicar estilos según el contenido"""
            if "🎾" in str(val):
                return 'background-color: #e8f5e8; color: #2e7d32; text-align: center; font-weight: bold; border: 1px solid #4caf50;'
            elif "⚪ Libre" in str(val):
                return 'background-color: #f5f5f5; color: #757575; text-align: center; border: 1px solid #e0e0e0;'
            elif "Hora" in str(val):
                return 'background-color: #1976d2; color: white; text-align: center; font-weight: bold; border: 1px solid #1565c0;'
            else:
                return 'text-align: center; font-weight: bold; border: 1px solid #2478CC; background-color: #e3f2fd;'

        # Mostrar tabla estilizada
        styled_df = df_calendar.style.applymap(style_calendar_table)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Leyenda
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("🎾 **Reservado** - Usuario asignado")
        with col2:
            st.markdown("⚪ **Libre** - Disponible para reservar")
        with col3:
            st.markdown(f"📊 **Total: {calendar_data['total_reservations']} reservas**")

    else:
        st.error("❌ Error cargando datos del calendario")

def mostrar_feedback_reserva(reservation_id):
    """Mostrar feedback de actualización de reserva"""
    feedback_key = f'actualizado_recientemente_{reservation_id}'
    if feedback_key in st.session_state:
        feedback = st.session_state[feedback_key]
        tiempo_transcurrido = (get_colombia_now() - feedback['timestamp']).total_seconds()

        if tiempo_transcurrido < 15:  # Mostrar por 15 segundos
            if feedback['accion'] == 'cancelada':
                st.success("✅ Reserva cancelada exitosamente y usuario notificado")
            return True
        else:
            # Limpiar feedback expirado
            del st.session_state[feedback_key]
    return False

def show_reservations_management_tab():
    """Gestión de reservas por usuario"""
    st.subheader("📅 Gestión de Reservas por Usuario")

    # Buscador de usuario
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Buscar usuario por nombre o email:",
            placeholder="Ingresa nombre o email del usuario",
            key="search_reservations_user"
        )

    with col2:
        search_button = st.button("🔍 Buscar", type="primary")

    if search_term and search_button:
        # Buscar usuarios que coincidan
        matching_users = admin_db_manager.search_users_for_reservations(search_term)

        if matching_users:
            if len(matching_users) == 1:
                st.session_state.selected_user_for_reservations = matching_users[0]
                st.session_state.matching_users_list = None  # Limpiar lista
            else:
                # Múltiples usuarios encontrados - guardar en session_state
                st.session_state.matching_users_list = matching_users
                # Limpiar selección anterior
                if 'selected_user_for_reservations' in st.session_state:
                    del st.session_state.selected_user_for_reservations
        else:
            st.warning("No se encontraron usuarios con ese criterio")
            st.session_state.matching_users_list = None

    # Mostrar lista de usuarios encontrados si hay múltiples
    if st.session_state.get('matching_users_list'):
        st.write("**Usuarios encontrados:**")
        for user in st.session_state.matching_users_list:
            # Usar email como parte de la key para hacer cada botón único
            button_key = f"select_user_{user['email'].replace('@', '_').replace('.', '_')}"
            if st.button(f"{user['name']} ({user['email']})", key=button_key):
                st.session_state.selected_user_for_reservations = user
                st.session_state.matching_users_list = None  # Limpiar lista después de seleccionar
                st.rerun()

    # Mostrar reservas del usuario seleccionado
    if 'selected_user_for_reservations' in st.session_state:
        user = st.session_state.selected_user_for_reservations

        st.markdown(f"### 📋 Reservas de {user['name']}")
        st.info(f"**Email:** {user['email']}")

        # Obtener reservas del usuario
        user_reservations = admin_db_manager.get_user_reservations_history(user['email'])

        for i, reservation in enumerate(user_reservations):
            # Formatear fecha más legible
            try:
                from datetime import datetime as dt
                fecha_obj = dt.strptime(reservation['date'], '%Y-%m-%d')
                fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
                dia_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha_obj.weekday()]
                fecha_display = f"{dia_semana} {fecha_formateada}"
            except:
                fecha_display = reservation['date']

            # Crear título del expander más claro
            titulo_expander = f"📅 {fecha_display} • 🕐 {reservation['hour']}:00"

            with st.expander(titulo_expander, expanded=False):
                # Info organizada en columnas
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    **📅 Fecha:** {fecha_display}  
                    **🕐 Hora:** {reservation['hour']}:00 - {reservation['hour'] + 1}:00  
                    **📝 Creada:** {reservation['created_at'][:10]}
                    """)

                with col2:
                    # Formulario para cancelación con motivo
                    with st.form(f"cancel_form_{reservation['id']}", clear_on_submit=True):
                        cancellation_reason = st.text_area(
                            "Motivo de cancelación (opcional):",
                            placeholder="Ej: Mantenimiento de cancha, lluvia, etc.",
                            max_chars=200,
                            key=f"reason_{reservation['id']}"
                        )

                        cancel_submitted = st.form_submit_button(
                            "❌ Cancelar Reserva",
                            type="secondary",
                            use_container_width=True
                        )

                        if cancel_submitted:
                            admin_user = st.session_state.get('admin_user', {})

                            with st.spinner("🔄 Cancelando reserva..."):
                                success = admin_db_manager.cancel_reservation_with_notification(
                                    reservation['id'],
                                    reservation['email'],
                                    cancellation_reason.strip() if cancellation_reason else "",
                                    admin_user.get('username', 'admin')
                                )

                                if success:
                                    st.success("✅ Reserva cancelada exitosamente y usuario notificado")
                                    # Limpiar selección
                                    if 'selected_user_for_reservations' in st.session_state:
                                        del st.session_state['selected_user_for_reservations']

                                    import time
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Error al cancelar reserva")

    st.divider()

    # NUEVA SECCIÓN: Historial de Cancelaciones
    st.subheader("📋 Historial de Cancelaciones")

    # Controles para el historial
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        days_back = st.selectbox(
            "Mostrar cancelaciones de:",
            options=[7, 15, 30, 60, 90],
            index=2,  # Default: 30 días
            format_func=lambda x: f"Últimos {x} días",
            key="cancellation_days_selector"
        )

    with col2:
        if st.button("🔄 Actualizar Historial", key="refresh_cancellations"):
            st.cache_data.clear()
            st.success("✅ Historial actualizado")

    with col3:
        show_all_cancellations = st.checkbox("Ver todas", key="show_all_cancellations")

    # Obtener historial de cancelaciones
    cancellations = admin_db_manager.get_cancellation_history(
        days_back if not show_all_cancellations else None
    )

    if cancellations:
        st.info(
            f"📊 **Total de cancelaciones:** {len(cancellations)} {'en todos los registros' if show_all_cancellations else f'en los últimos {days_back} días'}")

        # Convertir a DataFrame para mejor visualización
        import pandas as pd
        df_cancellations = pd.DataFrame(cancellations)

        # Renombrar columnas para display
        display_df = df_cancellations.rename(columns={
            'user_name': 'Usuario',
            'user_email': 'Email',
            'reservation_date': 'Fecha Reserva',
            'reservation_hour': 'Hora',
            'cancellation_reason': 'Motivo',
            'cancelled_by': 'Cancelado Por',
            'cancelled_at': 'Fecha Cancelación',
            'credits_refunded': 'Créditos Reembolsados'
        })

        # Seleccionar columnas a mostrar
        columns_to_show = [
            'Usuario', 'Email', 'Fecha Reserva', 'Hora', 'Motivo',
            'Cancelado Por', 'Fecha Cancelación', 'Créditos Reembolsados'
        ]

        # Mostrar tabla interactiva
        st.dataframe(
            display_df[columns_to_show],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Hora": st.column_config.TextColumn(
                    "Hora",
                    help="Hora de la reserva original",
                    width="small"
                ),
                "Motivo": st.column_config.TextColumn(
                    "Motivo",
                    help="Motivo de la cancelación",
                    width="medium"
                ),
                "Fecha Cancelación": st.column_config.DatetimeColumn(
                    "Fecha Cancelación",
                    help="Cuándo se canceló la reserva",
                    width="medium"
                ),
                "Créditos Reembolsados": st.column_config.NumberColumn(
                    "Créditos",
                    help="Créditos reembolsados",
                    width="small"
                )
            }
        )

        # Estadísticas adicionales
        with st.expander("📊 Estadísticas de Cancelaciones", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_refunds = df_cancellations['credits_refunded'].sum()
                st.metric("💰 Total Créditos Reembolsados", total_refunds)

            with col2:
                admin_cancellations = len(df_cancellations[df_cancellations['cancelled_by'] != 'system'])
                st.metric("👤 Cancelaciones Admin", admin_cancellations)

            with col3:
                with_reason = len(df_cancellations[
                                      (df_cancellations['cancellation_reason'].notna()) &
                                      (df_cancellations['cancellation_reason'] != 'Sin motivo especificado')
                                      ])
                st.metric("📝 Con Motivo Específico", with_reason)

            with col4:
                unique_users = df_cancellations['user_email'].nunique()
                st.metric("👥 Usuarios Afectados", unique_users)

    else:
        st.info(
            f"📅 No hay cancelaciones registradas {'en el período seleccionado' if not show_all_cancellations else ''}")

def mantener_expander_abierto_admin(item_id, accion='actualizacion', duracion=15):
    """Mantener expander abierto después de una acción administrativa"""
    key = f"expander_admin_{item_id}"
    st.session_state[key] = {
        'timestamp': get_colombia_now(),
        'accion': accion,
        'duracion': duracion
    }

def verificar_expander_abierto_admin(item_id):
    """Verificar si un expander debe mantenerse abierto"""
    key = f"expander_admin_{item_id}"
    if key in st.session_state:
        estado = st.session_state[key]
        tiempo_transcurrido = (get_colombia_now() - estado['timestamp']).total_seconds()
        if tiempo_transcurrido < estado['duracion']:
            return True
        else:
            del st.session_state[key]
    return False

def show_user_detailed_info(user):
    """Mostrar información detallada del usuario con feedback mejorado"""

    # Mostrar feedback si existe
    mostrar_feedback_usuario(user['id'])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **📊 Información General:**
        - **Nombre:** {user['full_name']}
        - **Email:** {user['email']}
        - **Créditos:** {user['credits'] or 0}
        - **Estado:** {'✅ Activo' if user['is_active'] else '❌ Inactivo'}
        - **Último login:** {user['last_login'][:10] if user['last_login'] else 'Nunca'}
        - **Registrado:** {user['created_at'][:10]}
        """)

    with col2:
        # Obtener estadísticas del usuario
        stats = admin_db_manager.get_user_stats(user['id'])
        st.markdown(f"""
        **📈 Estadísticas:**
        - **Total reservas:** {stats['total_reservations']}
        - **Reservas activas:** {stats['active_reservations']}
        - **Última reserva:** {stats['last_reservation'] or 'Nunca'}
        """)

    # Botón con callback
    status_text = "Desactiva" if user['is_active'] else "Activa"
    if st.button(f"🔄 {status_text} Usuario", key=f"toggle_{user['id']}"):
        with st.spinner(f"🔄 {status_text.lower()}ndo usuario..."):
            success = toggle_user_status_callback(user['id'], user['is_active'])
            if not success:
                st.error(f"❌ Error al {status_text.lower()} usuario")
            else:
                st.rerun()


def show_users_management_tab():
    """Gestión mejorada de usuarios con vista de base de datos siempre visible"""
    st.subheader("👥 Gestión de Usuarios")

    # Buscador en la parte superior
    col1, col2 = st.columns([3, 1])

    with col1:
        search_user = st.text_input("🔍 Buscar usuario por nombre o email:",
                                    placeholder="Ingresa nombre o email del usuario",
                                    key="search_users")

    with col2:
        if st.button("🔍 Buscar Usuario", type="primary"):
            if search_user:
                found_users = admin_db_manager.search_users_detailed(search_user)
                if found_users:
                    st.session_state.found_users = found_users
                else:
                    st.warning("No se encontraron usuarios")

    # Mostrar usuarios encontrados (si hay búsqueda)
    if 'found_users' in st.session_state and st.session_state.found_users:
        st.markdown("### 🔍 Resultados de Búsqueda")

        for user in st.session_state.found_users:
            expandido = verificar_expander_abierto_admin(user['id'])

            with st.expander(f"👤 {user['full_name']} ({user['email']})", expanded=expandido):
                show_user_detailed_info(user)

        st.divider()

    # Base de datos completa
    st.markdown("### 📊 Base de Usuarios Registrados")

    with st.spinner("Cargando datos de usuarios..."):
        users_stats = admin_db_manager.get_users_detailed_statistics()

    if users_stats:
        import pandas as pd

        df = pd.DataFrame(users_stats)
        df = df.rename(columns={
            'name': 'Nombre',
            'email': 'Email',
            'registered_date': 'Fecha Registro',
            'total_credits_bought': 'Créditos Comprados',
            'total_reservations': 'Reservas Totales',
            'favorite_day': 'Día Favorito',
            'favorite_time': 'Hora Favorita'
        })

        # Display with filters
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=True,
            column_config={
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                "Créditos Comprados": st.column_config.NumberColumn("Créditos Comprados", format="%d 💰"),
                "Reservas Totales": st.column_config.NumberColumn("Reservas Totales", format="%d 🎾"),
            }
        )

        # Summary stats
        st.markdown("### 📈 Estadísticas Generales")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Usuarios", len(users_stats))
        with col2:
            st.metric("Total Créditos Vendidos", sum(u['total_credits_bought'] for u in users_stats))
        with col3:
            st.metric("Total Reservas", sum(u['total_reservations'] for u in users_stats))
        with col4:
            avg_reservations = sum(u['total_reservations'] for u in users_stats) / len(
                users_stats) if users_stats else 0
            st.metric("Promedio Reservas/Usuario", f"{avg_reservations:.1f}")
    else:
        st.info("No hay usuarios registrados")

def show_credits_management_tab():
    """Gestión de créditos"""
    st.subheader("💰 Gestión de Créditos")

    # Estadísticas de créditos (mantener igual)
    credit_stats = admin_db_manager.get_credit_statistics()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{credit_stats['total_credits']}</div>
            <div class="stat-label">Créditos Totales en Sistema</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{credit_stats['credits_used_today']}</div>
            <div class="stat-label">Créditos Usados Hoy</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{credit_stats['users_with_credits']}</div>
            <div class="stat-label">Usuarios con Créditos</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # NUEVA SECCIÓN: Gestión mejorada de créditos
    st.subheader("💰 Gestionar Créditos de Usuario")

    # Inicializar session states si no existen
    if 'selected_user_for_credits' not in st.session_state:
        st.session_state.selected_user_for_credits = None
    if 'matching_users_credits' not in st.session_state:
        st.session_state.matching_users_credits = []

    # Buscador de usuario
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Buscar usuario por nombre o email:",
            placeholder="Ingresa nombre o email del usuario",
            key="search_credits_user"
        )

    with col2:
        if st.button("🔍 Buscar", type="primary", key="search_credits_btn"):
            if search_term:
                # Buscar usuarios que coincidan
                matching_users = admin_db_manager.search_users_for_credits(search_term)

                if matching_users:
                    if len(matching_users) == 1:
                        # Solo un usuario encontrado - seleccionar automáticamente
                        st.session_state.selected_user_for_credits = matching_users[0]
                        st.session_state.matching_users_credits = []
                        st.success(f"✅ Usuario seleccionado: {matching_users[0]['name']}")
                    else:
                        # Múltiples usuarios - guardar para mostrar
                        st.session_state.matching_users_credits = matching_users
                        st.session_state.selected_user_for_credits = None
                else:
                    st.warning("No se encontraron usuarios con ese criterio")
                    st.session_state.matching_users_credits = []
                    st.session_state.selected_user_for_credits = None

    # Mostrar lista de usuarios encontrados si hay múltiples
    if st.session_state.matching_users_credits:
        st.write("**Usuarios encontrados:**")

        for i, user in enumerate(st.session_state.matching_users_credits):
            with st.container():
                col_user, col_info, col_select = st.columns([2, 2, 1])

                with col_user:
                    st.write(f"**{user['name']}**")

                with col_info:
                    st.write(f"📧 {user['email']}")
                    st.write(f"🪙 {user['credits']} créditos")

                with col_select:
                    # Usar un key único y manejar la selección directamente
                    select_key = f"select_credit_user_{user['id']}_{i}"
                    if st.button("✅ Seleccionar", key=select_key):
                        st.session_state.selected_user_for_credits = user
                        st.session_state.matching_users_credits = []
                        st.rerun()

    # Mostrar usuario seleccionado y formulario de créditos
    selected_user = st.session_state.selected_user_for_credits

    if selected_user:
        # Mostrar información del usuario seleccionado
        st.markdown("### 👤 Usuario Seleccionado")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.info(f"**Nombre:** {selected_user['name']}")
        with col2:
            st.info(f"**Email:** {selected_user['email']}")
        with col3:
            st.info(f"**Créditos:** {selected_user['credits']}")

        # Formulario para gestionar créditos
        with st.form("manage_credits_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                operation = st.selectbox("Operación:", ["Agregar", "Quitar"])

            with col2:
                credits_amount = st.number_input("Cantidad:", min_value=1, max_value=100, value=1)

            with col3:
                reason = st.text_input("Motivo:", placeholder="Ej: Nueva Tiquetera")

            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_credits = st.form_submit_button(
                    f"💰 Confirmar",
                    type="primary",
                    use_container_width=True
                )

            if submit_credits:
                admin_user = st.session_state.get('admin_user', {})

                if operation == "Agregar":
                    success = admin_db_manager.add_credits_to_user(
                        selected_user['email'], credits_amount,
                        reason or "Créditos agregados por administrador",
                        admin_user.get('username', 'admin')
                    )
                    action_msg = f"agregados a"
                else:
                    success = admin_db_manager.remove_credits_from_user(
                        selected_user['email'], credits_amount,
                        reason or "Créditos removidos por administrador",
                        admin_user.get('username', 'admin')
                    )
                    action_msg = f"removidos de"

                if success:
                    st.success(f"✅ {credits_amount} créditos {action_msg} {selected_user['name']}")
                    send_credits_notification_email(
                        selected_user['email'], credits_amount, reason, operation.lower()
                    )

                    # Limpiar selección después del éxito
                    st.session_state.selected_user_for_credits = None
                    st.session_state.matching_users_credits = []

                    # Pequeña pausa para mostrar el mensaje
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    error_msg = "créditos insuficientes" if operation == "Quitar" else "error en la base de datos"
                    st.error(f"❌ Error: {error_msg}")

        # Botón para limpiar selección
        if st.button("🔄 Buscar Otro Usuario", type="secondary", key="clear_selection_credits"):
            st.session_state.selected_user_for_credits = None
            st.session_state.matching_users_credits = []
            st.rerun()

    else:
        # Mostrar instrucciones cuando no hay usuario seleccionado
        st.info("💡 Usa el buscador para encontrar y seleccionar un usuario")

    st.divider()

    # Historial de transacciones (mantener igual)
    st.subheader("📋 Historial de Transacciones")

    transactions = admin_db_manager.get_credit_transactions()
    if transactions:
        df_transactions = pd.DataFrame(transactions)
        df_transactions.columns = ['Usuario', 'Cantidad', 'Tipo', 'Descripción', 'Admin', 'Fecha y Hora']
        st.dataframe(df_transactions, use_container_width=True)
    else:
        st.info("No hay transacciones de créditos")

def send_cancellation_email(reservation):
    """Enviar email de cancelación de reserva"""
    try:
        if email_manager.is_configured():
            # Implementar envío de email de cancelación
            pass
    except Exception as e:
        st.warning(f"Error enviando email: {e}")

def send_reminder_email(reservation):
    """Enviar email recordatorio"""
    try:
        if email_manager.is_configured():
            # Implementar envío de recordatorio
            pass
    except Exception as e:
        st.warning(f"Error enviando recordatorio: {e}")

def send_credits_notification_email(user_email, credits_amount, reason, operation):
    """Enviar notificación de cambio de créditos"""
    try:
        if email_manager.is_configured():
            action = "agregados" if operation == "agregar" else "removidos"
            subject = f"🎾 Créditos {action.title()} - Sistema de Reservas"

            html_body = f"""
            <h2>Actualización de Créditos</h2>
            <p>Se han <strong>{action} {credits_amount} crédito(s)</strong> {'a' if operation == 'agregar' else 'de'} tu cuenta.</p>
            <p><strong>Motivo:</strong> {reason}</p>
            <p>Revisa tu saldo actual en la aplicación.</p>
            """

            email_manager.send_email(user_email, subject, html_body)
    except Exception as e:
        st.warning(f"Error enviando notificación: {e}")

def show_send_email_form(user):
    """Mostrar formulario para enviar email a usuario"""
    st.subheader(f"📧 Enviar Email a {user['Nombre']}")
    # Implementar formulario de email

def show_user_history(user_id):
    """Mostrar historial de usuario"""
    st.subheader("📊 Historial de Usuario")
    # Implementar vista de historial

def toggle_user_status_callback(user_id, current_status):
    """Callback para cambiar estado de usuario"""
    status_text = "desactivado" if current_status else "activado"

    if admin_db_manager.toggle_user_status_with_notification(user_id):
        # Marcar que se actualizó recientemente
        st.session_state[f'usuario_actualizado_recientemente_{user_id}'] = {
            'timestamp': get_colombia_now(),
            'accion': 'cambio_estado',
            'mensaje': f"Usuario {status_text} y notificado por email"
        }

        # Marcar expander para mantenerlo abierto
        mantener_expander_abierto_admin(user_id, 'cambio_estado', 15)

        # Actualizar lista
        if 'found_users' in st.session_state:
            for i, u in enumerate(st.session_state.found_users):
                if u['id'] == user_id:
                    st.session_state.found_users[i]['is_active'] = not current_status
                    break

        return True
    return False

def mostrar_feedback_usuario(user_id):
    """Mostrar feedback de actualización de usuario"""
    feedback_key = f'usuario_actualizado_recientemente_{user_id}'
    if feedback_key in st.session_state:
        feedback = st.session_state[feedback_key]
        tiempo_transcurrido = (get_colombia_now() - feedback['timestamp']).total_seconds()

        if tiempo_transcurrido < 15:  # Mostrar por 15 segundos
            st.success(f"✅ {feedback['mensaje']}")
            return True
        else:
            # Limpiar feedback expirado
            del st.session_state[feedback_key]
    return False

def show_config_tab():
    """Mostrar pestaña de configuración del sistema"""
    st.subheader("⚙️ Configuración del Sistema")

    # Header estilizado
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    ">
        <h3 style="margin: 0; color: #495057;">🔐 Gestión de Contraseña del Candado</h3>
        <p style="margin: 10px 0 0 0; color: #6c757d;">Esta contraseña se enviará en los emails de confirmación de reserva</p>
    </div>
    """, unsafe_allow_html=True)

    # Layout principal
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # MOVER LA OBTENCIÓN FUERA DEL FORMULARIO
        current_lock_code = admin_db_manager.get_current_lock_code()

        # Card para mostrar contraseña actual - FUERA del formulario
        if current_lock_code:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 2px solid #28a745;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
                box-shadow: 0 4px 8px rgba(40, 167, 69, 0.2);
            ">
                <h4 style="margin: 0; color: #155724;">
                    <i class="fas fa-lock"></i> Contraseña Actual
                </h4>
                <div style="
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #155724;
                    margin: 15px 0;
                    font-family: 'Courier New', monospace;
                    background: white;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                ">
                    {current_lock_code}
                </div>
                <small style="color: #155724; opacity: 0.8;">
                    Esta contraseña se incluye en los emails de confirmación
                </small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                border: 2px solid #dc3545;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
                box-shadow: 0 4px 8px rgba(220, 53, 69, 0.2);
            ">
                <h4 style="margin: 0; color: #721c24;">
                    <i class="fas fa-exclamation-triangle"></i> Sin Contraseña
                </h4>
                <p style="margin: 10px 0 0 0; color: #721c24;">
                    No hay contraseña configurada para el candado
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Formulario SOLO para actualizar - SIN mostrar contraseña actual
        with st.form("advanced_lock_code_form", clear_on_submit=True):  # clear_on_submit=True
            st.markdown("**Actualizar contraseña del candado:**")

            # Input con estilo mejorado
            new_lock_code = st.text_input(
                "Nueva contraseña del candado",
                placeholder="Ingresa 4 dígitos (ej: 1234)",
                max_chars=4,
                help="La contraseña debe ser exactamente 4 dígitos numéricos",
                label_visibility="collapsed"
            )

            # Validación en tiempo real
            if new_lock_code:
                if len(new_lock_code) == 4 and new_lock_code.isdigit():
                    st.success("✅ Formato válido")
                else:
                    if len(new_lock_code) < 4:
                        st.warning(f"⚠️ Faltan {4 - len(new_lock_code)} dígito(s)")
                    elif len(new_lock_code) > 4:
                        st.error("❌ Máximo 4 dígitos")
                    elif not new_lock_code.isdigit():
                        st.error("❌ Solo se permiten números")

            st.markdown("<br>", unsafe_allow_html=True)

            # Botón de actualización estilizado
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_button = st.form_submit_button(
                    "🔄 Actualizar Contraseña",
                    type="primary",
                    use_container_width=True
                )

            if submit_button:
                if not new_lock_code:
                    st.error("❌ Por favor ingresa una contraseña")
                elif len(new_lock_code) != 4:
                    st.error("❌ La contraseña debe tener exactamente 4 dígitos")
                elif not new_lock_code.isdigit():
                    st.error("❌ La contraseña solo puede contener números")
                else:
                    # Intentar actualizar
                    admin_user = st.session_state.get('admin_user', {})

                    with st.spinner("🔄 Actualizando contraseña..."):
                        success = admin_db_manager.update_lock_code(
                            new_lock_code,
                            admin_user.get('username', 'admin')
                        )

                    if success:
                        st.success("✅ Contraseña actualizada exitosamente")
                        st.balloons()

                        # Forzar actualización completa
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar la contraseña. Intenta de nuevo.")

        # Información adicional
        with st.expander("ℹ️ Información sobre la contraseña del candado", expanded=False):
            st.markdown("""
            **¿Para qué sirve esta contraseña?**
            - Se incluye en todos los emails de confirmación de reserva
            - Los usuarios la necesitan para abrir el candado de la cancha
            - Es importante mantenerla actualizada y comunicarla cuando sea necesario

            **Recomendaciones:**
            - Usa 4 dígitos fáciles de recordar pero no obvios
            - Cambia la contraseña periódicamente por seguridad
            - Evita secuencias simples como 1234 o 0000

            **Historial de cambios:**
            - Los cambios quedan registrados con fecha y administrador
            - Puedes ver el historial en la base de datos si es necesario
            """)

    st.markdown("---")

    # Código de Acceso para Primer Login
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        ">
            <h3 style="margin: 0; color: #495057;">🔐 Código de Acceso Primer Login</h3>
            <p style="margin: 10px 0 0 0; color: #6c757d;">Código requerido para usuarios en su primer acceso al sistema</p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Mostrar código actual
        current_access_code = admin_db_manager.get_current_access_code()

        if current_access_code:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
                    border: 2px solid #17a2b8;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(23, 162, 184, 0.2);
                ">
                    <h4 style="margin: 0; color: #0c5460;">
                        <i class="fas fa-key"></i> Código de Acceso Actual
                    </h4>
                    <div style="
                        font-size: 2.5rem;
                        font-weight: bold;
                        color: #0c5460;
                        margin: 15px 0;
                        font-family: 'Courier New', monospace;
                        background: white;
                        border-radius: 8px;
                        padding: 15px;
                        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        {current_access_code}
                    </div>
                    <small style="color: #0c5460; opacity: 0.8;">
                        Proporciona este código a nuevos usuarios para su primer acceso
                    </small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                    border: 2px solid #dc3545;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                ">
                    <h4 style="margin: 0; color: #721c24;">
                        <i class="fas fa-exclamation-triangle"></i> Sin Código de Acceso
                    </h4>
                    <p style="margin: 10px 0 0 0; color: #721c24;">
                        No hay código de acceso configurado
                    </p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Formulario para actualizar código
        with st.form("access_code_form", clear_on_submit=True):
            st.markdown("**Actualizar código de acceso:**")

            new_access_code = st.text_input(
                "Nuevo código de acceso",
                placeholder="Ingresa 6 caracteres (ej: ABC123)",
                max_chars=6,
                help="El código debe ser exactamente 6 caracteres (letras y números)",
                label_visibility="collapsed"
            )

            # Validación en tiempo real
            if new_access_code:
                if len(new_access_code) == 6:
                    st.success("✅ Formato válido")
                else:
                    if len(new_access_code) < 6:
                        st.warning(f"⚠️ Faltan {6 - len(new_access_code)} caracter(es)")
                    else:
                        st.error("❌ Máximo 6 caracteres")

            st.markdown("<br>", unsafe_allow_html=True)

            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_button = st.form_submit_button(
                    "🔄 Actualizar Código",
                    type="primary",
                    use_container_width=True
                )

            if submit_button:
                if not new_access_code:
                    st.error("❌ Por favor ingresa un código")
                elif len(new_access_code) != 6:
                    st.error("❌ El código debe tener exactamente 6 caracteres")
                else:
                    admin_user = st.session_state.get('admin_user', {})

                    with st.spinner("🔄 Actualizando código..."):
                        success = admin_db_manager.update_access_code(
                            new_access_code.upper(),
                            admin_user.get('username', 'admin')
                        )

                    if success:
                        st.success("✅ Código de acceso actualizado exitosamente")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar el código. Intenta de nuevo.")

        # Información adicional
        with st.expander("ℹ️ Información sobre el código de acceso", expanded=False):
            st.markdown("""
                **¿Para qué sirve este código?**
                - Se requiere únicamente en el primer login de cada usuario
                - Después del primer acceso exitoso, ya no se pedirá más
                - Ayuda a controlar el acceso inicial al sistema

                **Recomendaciones:**
                - Usa 6 caracteres fáciles de comunicar
                - Combina letras y números para mayor seguridad
                - Cambia el código periódicamente
                - Comunica el código de manera segura a nuevos usuarios

                **Proceso:**
                1. Nuevo usuario se registra normalmente
                2. En su primer login, se le pide este código
                3. Una vez ingresado correctamente, nunca más se le pedirá
                """)

    st.markdown("---")



    # Gestión de Usuarios del comité
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        ">
            <h3 style="margin: 0; color: #495057;">⭐ Gestión de usuarios que pertenecen al comité</h3>
            <p style="margin: 10px 0 0 0; color: #6c757d;">Los usuarios del comité pueden reservar de 8:00 AM a 8:00 PM</p>
        </div>
        """, unsafe_allow_html=True)

    # Mostrar usuarios VIP actuales
    vip_users = admin_db_manager.get_vip_users()

    if vip_users:
        st.subheader("🏛️ Usuarios que pertenecen al comité")
        for user in vip_users:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📧 {user['email']}")
            with col2:
                if st.button("❌ Remover", key=f"remove_vip_{user['id']}"):
                    if admin_db_manager.remove_vip_user(user['email']):
                        st.success(f"Usuario removido del Comité: {user['email']}")
                        st.rerun()
                    else:
                        st.error("Error removiendo usuario VIP")

    # Formulario para agregar nuevo usuario al comité
    with st.form("add_vip_user_form", clear_on_submit=True):
        st.markdown("**Agregar nuevo usuario al comité:**")
        new_vip_email = st.text_input(
            "Email del usuario",
            placeholder="usuario@ejemplo.com",
            help="El usuario debe estar registrado en el sistema"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.form_submit_button("⭐ Agregar al comité", type="primary", use_container_width=True):
                if new_vip_email:
                    admin_user = st.session_state.get('admin_user', {})
                    if admin_db_manager.add_vip_user(new_vip_email, admin_user.get('username', 'admin')):
                        st.success(f"✅ Usuario agregado al comité: {new_vip_email}")
                        st.rerun()
                    else:
                        st.error("❌ Error agregando usuario (puede que ya sea parte del comité o no exista)")
                else:
                    st.error("Por favor ingresa un email válido")


def show_maintenance_tab():
    """Mostrar pestaña de gestión de mantenimiento"""
    st.subheader("🔧 Gestión de Mantenimiento de Cancha")

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    ">
        <h3 style="margin: 0; color: #495057;">🔧 Programar Mantenimiento</h3>
        <p style="margin: 10px 0 0 0; color: #6c757d;">Bloquea horarios cuando la cancha no esté disponible</p>
    </div>
    """, unsafe_allow_html=True)

    # Formulario para agregar mantenimiento
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("add_maintenance_form", clear_on_submit=True):
            st.markdown("**Programar nuevo mantenimiento:**")

            # Selector de fecha
            maintenance_date = st.date_input(
                "Fecha de mantenimiento",
                min_value=get_colombia_today(),
                help="Selecciona la fecha para el mantenimiento"
            )

            # Opción de día completo
            is_whole_day = st.checkbox(
                "🔧 Mantenimiento de día completo (6:00 - 22:00)",
                help="Bloquea todas las horas del día (6:00 AM a 10:00 PM)"
            )

            # Selectores de rango de horas (solo si no es día completo)
            if not is_whole_day:
                col_start, col_end = st.columns(2)

                with col_start:
                    start_hour = st.selectbox(
                        "Hora de inicio",
                        options=list(range(6, 22)),
                        format_func=lambda x: f"{x:02d}:00",
                        help="Hora de inicio del mantenimiento"
                    )

                with col_end:
                    end_hour = st.selectbox(
                        "Hora de fin",
                        options=list(range(7, 23)),
                        index=min(15-7, len(list(range(7, 23)))-1),  # Default a las 3 PM
                        format_func=lambda x: f"{x:02d}:00",
                        help="Hora de fin del mantenimiento (no incluida)"
                    )

                # Mostrar resumen del rango
                if start_hour < end_hour:
                    hours_count = end_hour - start_hour
                    st.info(f"📊 Se bloquearán {hours_count} hora(s): {start_hour}:00 - {end_hour}:00")
                else:
                    st.warning("⚠️ La hora de inicio debe ser menor que la hora de fin")
            else:
                st.info("📊 Se bloquearán 16 horas: 6:00 - 22:00 (día completo)")
                start_hour = 6
                end_hour = 22

            # Motivo
            maintenance_reason = st.text_area(
                "Motivo del mantenimiento",
                placeholder="Ej: Limpieza profunda, reparación de superficie, pintura, etc.",
                max_chars=200
            )

            # Botón de submit
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_button = st.form_submit_button(
                    "🔧 Programar Mantenimiento",
                    type="primary",
                    use_container_width=True
                )

            if submit_button:
                # Validar horas
                if not is_whole_day and start_hour >= end_hour:
                    st.error("❌ La hora de inicio debe ser menor que la hora de fin")
                else:
                    admin_user = st.session_state.get('admin_user', {})

                    success, message = admin_db_manager.add_maintenance_slot(
                        maintenance_date.strftime('%Y-%m-%d'),
                        start_hour,
                        end_hour,
                        maintenance_reason.strip() if maintenance_reason else "Mantenimiento programado",
                        admin_user.get('username', 'admin'),
                        is_whole_day
                    )

                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    st.markdown("---")

    # Mostrar mantenimientos programados
    st.subheader("📋 Mantenimientos Programados")

    # Controles
    col1, col2 = st.columns([2, 1])

    with col1:
        days_range = st.selectbox(
            "Mostrar mantenimientos de:",
            options=[7, 15, 30, 60, 90],
            index=1,
            format_func=lambda x: f"Próximos {x} días"
        )

    with col2:
        if st.button("🔄 Actualizar", key="refresh_maintenance"):
            st.cache_data.clear()
            st.success("✅ Actualizado")

    # Obtener mantenimientos
    from datetime import timedelta
    start_date = get_colombia_today().strftime('%Y-%m-%d')
    end_date = (get_colombia_today() + timedelta(days=days_range)).strftime('%Y-%m-%d')

    maintenance_slots = admin_db_manager.get_maintenance_slots(start_date, end_date)

    if maintenance_slots:
        st.info(f"📊 Total de mantenimientos programados: {len(maintenance_slots)}")

        # Mostrar cada mantenimiento
        for slot in maintenance_slots:
            # Formatear fecha
            try:
                from datetime import datetime as dt
                date_obj = dt.strptime(slot['date'], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
                day_name = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][date_obj.weekday()]
                date_display = f"{day_name} {formatted_date}"
            except:
                date_display = slot['date']

            # Determinar el tipo de mantenimiento y formato de hora
            maintenance_type = slot.get('maintenance_type', 'single_hour')
            start_hour = slot.get('start_hour', slot.get('hour', 6))
            end_hour = slot.get('end_hour', slot.get('hour', 6) + 1)

            if maintenance_type == 'whole_day':
                hour_display = "🌅 DÍA COMPLETO (6:00 - 22:00)"
                type_badge = "🔧 Día Completo"
            elif maintenance_type == 'time_range':
                hour_display = f"⏰ {start_hour:02d}:00 - {end_hour:02d}:00"
                hours_count = slot.get('hour_count', end_hour - start_hour)
                type_badge = f"⏱️ Rango ({hours_count}h)"
            else:
                hour_display = f"{start_hour:02d}:00 - {end_hour:02d}:00"
                type_badge = "🕐 Individual"

            with st.expander(f"🔧 {date_display} • {hour_display}", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"""
                    **📅 Fecha:** {date_display}
                    **🕐 Horario:** {hour_display}
                    **🏷️ Tipo:** {type_badge}
                    **📝 Motivo:** {slot.get('reason', 'No especificado')}
                    **👤 Programado por:** {slot.get('created_by', 'N/A')}
                    **📆 Creado:** {slot.get('created_at', 'N/A')}
                    """)

                    # Mostrar detalles de horas individuales bloqueadas si es rango
                    if maintenance_type in ['time_range', 'whole_day']:
                        hours_list = slot.get('hours_list', [])
                        if hours_list:
                            st.caption(f"🔒 Horas bloqueadas: {', '.join([f'{h:02d}:00' for h in sorted(hours_list)])}")

                with col2:
                    # Botón para eliminar
                    delete_key = f"delete_maintenance_{slot['date']}_{start_hour}_{end_hour}"
                    if st.button("🗑️ Eliminar", key=delete_key):
                        # Si es un rango, eliminar todos los slots del rango
                        if maintenance_type in ['time_range', 'whole_day']:
                            success, message = admin_db_manager.remove_maintenance_range(
                                slot['date'], start_hour, end_hour
                            )
                            if success:
                                st.success(f"✅ {message}")
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        else:
                            # Eliminar slot individual
                            if admin_db_manager.remove_maintenance_slot(slot['id']):
                                st.success("✅ Mantenimiento eliminado")
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Error al eliminar")
    else:
        st.info("📅 No hay mantenimientos programados en este período")

def main():
    """Función principal de la aplicación de administración"""
    setup_admin_page_config()
    apply_admin_styles()

    # Validate admin security configuration first
    if not admin_auth_manager.validate_admin_config():
        st.error("🚨 Admin security configuration failed")
        st.stop()

    # Ensure admin user exists with secure credentials
    if not admin_auth_manager.ensure_admin_user_exists():
        st.error("🚨 Failed to initialize admin user")
        st.stop()

    # Verificar autenticación
    if not require_admin_auth():
        show_admin_login()
    else:
        show_admin_dashboard()


if __name__ == "__main__":
    main()