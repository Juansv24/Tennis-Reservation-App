"""
Aplicación de Administración para Sistema de Reservas de Cancha de Tenis
Gestión de reservas, usuarios y créditos
"""

import streamlit as st
import datetime
from datetime import timedelta
import pandas as pd
from admin_auth import admin_auth_manager, require_admin_auth
from admin_database import admin_db_manager
from timezone_utils import get_colombia_today, get_colombia_now
from email_config import email_manager

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
                    import pandas as pd
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
                    from datetime import datetime
                    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
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
        ["📊 Dashboard", "📅 Reservas", "👥 Usuarios", "💰 Créditos", "⚙️ Config"],
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
        st.subheader("📈 Reservas por Día (Últimos 7 días)")
        daily_stats = admin_db_manager.get_daily_reservation_stats()
        if daily_stats:
            df_daily = pd.DataFrame(daily_stats)
            st.bar_chart(df_daily.set_index('date')['count'])
        else:
            st.info("No hay datos de reservas disponibles")

    with col2:
        st.subheader("⏰ Horas Más Populares")
        hourly_stats = admin_db_manager.get_hourly_reservation_stats()
        if hourly_stats:
            df_hourly = pd.DataFrame(hourly_stats)
            st.bar_chart(df_hourly.set_index('hour')['count'])
        else:
            st.info("No hay datos de horarios disponibles")

    st.divider()

    # Estadísticas de usuarios
    col1, col2 = st.columns(2)

    with col1:
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
            from datetime import datetime
            try:
                fecha_obj = datetime.strptime(reservation['date'], '%Y-%m-%d')
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
                    if st.button("❌ Cancelar Reserva",
                                 key=f"cancel_{reservation['id']}",
                                 type="secondary",
                                 use_container_width=True):
                            with st.spinner("🔄 Cancelando reserva..."):
                                if admin_db_manager.cancel_reservation(reservation['id']):
                                    # Obtener datos del usuario para el email
                                    user_data = admin_db_manager.get_user_by_email(reservation['email'])

                                    # Enviar email de cancelación
                                    try:
                                        if email_manager.is_configured() and user_data:
                                            subject = "🎾 Reserva Cancelada - Sistema de Reservas"
                                            html_body = f"""
                                            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                                                <div style="background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 20px; text-align: center; border-radius: 10px;">
                                                    <h1>🎾 Reserva Cancelada</h1>
                                                </div>

                                                <div style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0;">
                                                    <h2>Hola {user_data['full_name']},</h2>
                                                    <p>Tu reserva ha sido <strong>cancelada por el administrador</strong>:</p>

                                                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 5px solid #FFD400;">
                                                        <p><strong>📅 Fecha:</strong> {reservation['date']}</p>
                                                        <p><strong>🕐 Hora:</strong> {reservation['hour']}:00</p>
                                                    </div>

                                                    <p>✅ <strong>Se ha reembolsado 1 crédito</strong> a tu cuenta automáticamente.</p>
                                                    <p>Si tienes preguntas, contacta al administrador.</p>
                                                </div>
                                            </div>
                                            """

                                            success, message = email_manager.send_email(reservation['email'], subject,
                                                                                        html_body)
                                            if success:
                                                st.success(
                                                    "✅ Reserva cancelada exitosamente y usuario notificado por email")
                                            else:
                                                st.success("✅ Reserva cancelada exitosamente")
                                                st.warning(f"⚠️ Error enviando email: {message}")
                                        else:
                                            st.success("✅ Reserva cancelada exitosamente (email no configurado)")

                                    except Exception as e:
                                        st.success("✅ Reserva cancelada exitosamente")
                                        st.warning(f"⚠️ Error enviando notificación: {str(e)}")

                                    # Limpiar y recargar la lista
                                    if 'selected_user_for_reservations' in st.session_state:
                                        del st.session_state['selected_user_for_reservations']

                                    # Pequeña pausa para que el usuario vea el mensaje
                                    import time
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Error al cancelar reserva")

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
    """Gestión mejorada de usuarios"""
    st.subheader("👥 Gestión de Usuarios")

    # Buscador
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

    # Mostrar usuarios encontrados
    if 'found_users' in st.session_state and st.session_state.found_users:
        st.write("**Usuarios encontrados:**")

        for user in st.session_state.found_users:
            # Verificar si debe mantenerse abierto
            expandido = verificar_expander_abierto_admin(user['id'])

            with st.expander(f"👤 {user['full_name']} ({user['email']})", expanded=expandido):
                show_user_detailed_info(user)

def show_credits_management_tab():
    """Gestión de créditos"""
    st.subheader("💰 Gestión de Créditos")

    # Estadísticas de créditos
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

    # Sección para gestionar créditos
    st.subheader("💰 Gestionar Créditos de Usuario")

    with st.form("manage_credits_form"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            user_email = st.text_input("Email del usuario:")

        with col2:
            operation = st.selectbox("Operación:", ["Agregar", "Quitar"])

        with col3:
            credits_amount = st.number_input("Cantidad:", min_value=1, max_value=100, value=1)

        with col4:
            reason = st.text_input("Motivo:", placeholder="Ej: Nueva Tiquetera")

        if st.form_submit_button("💰 Aplicar Cambio", type="primary"):
            if user_email and credits_amount:
                admin_user = st.session_state.get('admin_user', {})

                if operation == "Agregar":
                    success = admin_db_manager.add_credits_to_user(
                        user_email, credits_amount, reason or "Créditos agregados por administrador",
                        admin_user.get('username', 'admin')
                    )
                    action_msg = f"agregados a"
                else:
                    success = admin_db_manager.remove_credits_from_user(
                        user_email, credits_amount, reason or "Créditos removidos por administrador",
                        admin_user.get('username', 'admin')
                    )
                    action_msg = f"removidos de"

                if success:
                    st.success(f"✅ {credits_amount} créditos {action_msg} {user_email}")
                    send_credits_notification_email(user_email, credits_amount, reason, operation.lower())
                    st.rerun()
                else:
                    error_msg = "créditos insuficientes" if operation == "Quitar" else "error en la base de datos"
                    st.error(f"❌ Error: Usuario no encontrado o {error_msg}")
            else:
                st.error("Por favor completa todos los campos")

    st.divider()

    # Historial de transacciones de créditos
    st.subheader("📋 Historial de Transacciones")

    transactions = admin_db_manager.get_credit_transactions()
    if transactions:
        df_transactions = pd.DataFrame(transactions)
        df_transactions.columns = ['Usuario', 'Cantidad', 'Tipo', 'Descripción', 'Admin', 'Fecha']
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