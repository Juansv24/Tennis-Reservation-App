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
                "🚪 Iniciar Sesión",
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

        # Credenciales de prueba
        with st.expander("💡 Credenciales de prueba"):
            st.info("""
            **Para fines de demostración:**

            👤 **Usuario:** `admin`

            🔑 **Contraseña:** `tennis123`
            """)


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

    # Barra superior con logout
    col1, col2, col3 = st.columns([3, 2, 1])

    with col2:
        current_time = get_colombia_now()
        st.caption(f"🕐 {current_time.strftime('%d/%m/%Y %H:%M:%S')}")

    with col3:
        if st.button("🚪 Cerrar Sesión", type="secondary"):
            admin_auth_manager.logout_admin()
            st.rerun()

    # Control de navegación segmentado
    tab = st.segmented_control(
        "Navegación Admin",
        ["📊 Dashboard", "📅 Reservas", "👥 Usuarios", "💰 Créditos"],
        selection_mode="single",
        default="📊 Dashboard",
        label_visibility="collapsed",
    )

    st.divider()

    # Mostrar sección correspondiente
    if tab == "📊 Dashboard":
        show_dashboard_tab()
    elif tab == "📅 Reservas":
        show_reservations_management_tab()
    elif tab == "👥 Usuarios":
        show_users_management_tab()
    elif tab == "💰 Créditos":
        show_credits_management_tab()


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
                st.write(f"{i}. **{user['name']}** - {user['reservations']} reservas")
        else:
            st.info("No hay datos de usuarios disponibles")


def show_reservations_management_tab():
    """Gestión de reservas por usuario"""
    st.subheader("📅 Gestión de Reservas por Usuario")

    # Buscador de usuario
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Buscar usuario por nombre o email:",
            placeholder="Ingresa nombre o email del usuario"
        )

    with col2:
        search_button = st.button("🔍 Buscar", type="primary")

    if search_term and search_button:
        # Buscar usuarios que coincidan
        matching_users = admin_db_manager.search_users_for_reservations(search_term)

        if matching_users:
            if len(matching_users) == 1:
                st.session_state.selected_user_for_reservations = matching_users[0]
            else:
                # Múltiples usuarios encontrados
                st.write("**Usuarios encontrados:**")
                for i, user in enumerate(matching_users):
                    if st.button(f"{user['name']} ({user['email']})", key=f"user_{i}"):
                        st.session_state.selected_user_for_reservations = user
                        st.rerun()
        else:
            st.warning("No se encontraron usuarios con ese criterio")

    # Mostrar reservas del usuario seleccionado
    if 'selected_user_for_reservations' in st.session_state:
        user = st.session_state.selected_user_for_reservations

        st.markdown(f"### 📋 Reservas de {user['name']}")
        st.info(f"**Email:** {user['email']}")

        # Obtener reservas del usuario
        user_reservations = admin_db_manager.get_user_reservations_history(user['email'])

        if user_reservations:
            # Mostrar cada reserva con opciones
            for i, reservation in enumerate(user_reservations):
                with st.expander(f"Reserva: {reservation['date']} - {reservation['hour']}:00"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Fecha:** {reservation['date']}")
                        st.write(f"**Hora:** {reservation['hour']}:00")
                        st.write(f"**Creada:** {reservation['created_at'][:10]}")

                    with col2:
                        if st.button("📝 Modificar", key=f"modify_{reservation['id']}"):
                            st.session_state.modifying_reservation = reservation
                            st.rerun()

                    with col3:
                        if st.button("❌ Cancelar", key=f"cancel_{reservation['id']}", type="secondary"):
                            if admin_db_manager.cancel_reservation(reservation['id']):
                                st.success("Reserva cancelada exitosamente")
                                # Invalidar cache si existe
                                if 'selected_user_for_reservations' in st.session_state:
                                    del st.session_state['selected_user_for_reservations']
                                st.rerun()
                            else:
                                st.error("Error al cancelar reserva")
        else:
            st.info("Este usuario no tiene reservas")


def show_user_detailed_info(user):
    """Mostrar información detallada del usuario"""
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

    # Acciones
    col1, col2 = st.columns(2)

    with col1:
        status_text = "Desactivar" if user['is_active'] else "Activar"
        if st.button(f"🔄 {status_text} Usuario", key=f"toggle_{user['id']}"):
            if admin_db_manager.toggle_user_status_with_notification(user['id']):
                st.success(f"Usuario {status_text.lower()}do y notificado")
                # Actualizar lista
                if 'found_users' in st.session_state:
                    del st.session_state.found_users
                st.rerun()

    with col2:
        if st.button("📧 Enviar Email", key=f"email_{user['id']}"):
            st.session_state[f"show_email_form_{user['id']}"] = True

    # Mostrar reservas recientes
    recent_reservations = admin_db_manager.get_user_recent_reservations(user['email'])
    if recent_reservations:
        st.write("**🕐 Reservas Recientes:**")
        for res in recent_reservations[:5]:
            st.write(f"• {res['date']} - {res['hour']}:00")

def show_users_management_tab():
    """Gestión mejorada de usuarios"""
    st.subheader("👥 Gestión de Usuarios")

    # Buscador
    col1, col2 = st.columns([3, 1])

    with col1:
        search_user = st.text_input("🔍 Buscar usuario por nombre o email:")

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
            with st.expander(f"👤 {user['full_name']} ({user['email']})"):
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


def main():
    """Función principal de la aplicación de administración"""
    setup_admin_page_config()
    apply_admin_styles()

    # Verificar autenticación
    if not require_admin_auth():
        show_admin_login()
    else:
        show_admin_dashboard()


if __name__ == "__main__":
    main()