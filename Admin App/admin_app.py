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
    if 'admin_selected_section' not in st.session_state:
        st.session_state.admin_selected_section = "Dashboard"

    selected_section = st.segmented_control(
        label="Navegación",
        options=[
            "Dashboard",
            "Reservas",
            "Usuarios",
            "Créditos"
        ],
        default=st.session_state.admin_selected_section,
        key="admin_navigation"
    )

    # Actualizar estado si cambió la selección
    if selected_section != st.session_state.admin_selected_section:
        st.session_state.admin_selected_section = selected_section

    st.divider()

    # Mostrar sección correspondiente
    if selected_section == "Dashboard":
        show_dashboard_tab()
    elif selected_section == "Reservas":
        show_reservations_management_tab()
    elif selected_section == "Usuarios":
        show_users_management_tab()
    elif selected_section == "Créditos":
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


def show_reservations_management_tab():
    """Gestión de reservas"""
    st.subheader("📅 Gestión de Reservas")

    # Filtros
    col1, col2, col3 = st.columns(3)

    with col1:
        date_filter = st.date_input(
            "Fecha",
            value=get_colombia_today(),
            min_value=get_colombia_today() - timedelta(days=30),
            max_value=get_colombia_today() + timedelta(days=30)
        )

    with col2:
        status_filter = st.selectbox(
            "Estado",
            ["Todas", "Activas", "Futuras", "Pasadas"]
        )

    with col3:
        if st.button("🔄 Actualizar", type="primary"):
            st.rerun()

    # Obtener reservas
    reservations = admin_db_manager.get_reservations_for_admin(date_filter, status_filter)

    if reservations:
        st.write(f"**Total: {len(reservations)} reservas**")

        # Mostrar reservas en tabla
        df = pd.DataFrame(reservations)
        df.columns = ['ID', 'Fecha', 'Hora', 'Usuario', 'Email', 'Creada']

        # Hacer la tabla interactiva
        selected_reservation = st.selectbox(
            "Seleccionar reserva para gestionar:",
            options=range(len(df)),
            format_func=lambda x: f"{df.iloc[x]['Fecha']} - {df.iloc[x]['Hora']}:00 - {df.iloc[x]['Usuario']}"
        )

        if selected_reservation is not None:
            reservation = df.iloc[selected_reservation]

            col1, col2 = st.columns(2)

            with col1:
                if st.button("❌ Cancelar Reserva", type="secondary"):
                    if admin_db_manager.cancel_reservation(reservation['ID']):
                        # Enviar email de notificación
                        send_cancellation_email(reservation)
                        st.success("Reserva cancelada exitosamente")
                        st.rerun()
                    else:
                        st.error("Error al cancelar la reserva")

            with col2:
                if st.button("📧 Enviar Recordatorio"):
                    send_reminder_email(reservation)
                    st.success("Recordatorio enviado")

        # Mostrar tabla completa
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay reservas para los filtros seleccionados")


def show_users_management_tab():
    """Gestión de usuarios"""
    st.subheader("👥 Gestión de Usuarios")

    # Obtener usuarios
    users = admin_db_manager.get_all_users()

    if users:
        df_users = pd.DataFrame(users)
        df_users.columns = ['ID', 'Email', 'Nombre', 'Créditos', 'Activo', 'Último Login', 'Creado']

        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            search_email = st.text_input("🔍 Buscar por email:")
        with col2:
            status_filter = st.selectbox("Estado:", ["Todos", "Activos", "Inactivos"])

        # Aplicar filtros
        if search_email:
            df_users = df_users[df_users['Email'].str.contains(search_email, case=False, na=False)]

        if status_filter != "Todos":
            is_active = status_filter == "Activos"
            df_users = df_users[df_users['Activo'] == is_active]

        st.write(f"**Total: {len(df_users)} usuarios**")

        # Seleccionar usuario para gestionar
        if len(df_users) > 0:
            selected_user_idx = st.selectbox(
                "Seleccionar usuario:",
                options=range(len(df_users)),
                format_func=lambda x: f"{df_users.iloc[x]['Nombre']} ({df_users.iloc[x]['Email']})"
            )

            if selected_user_idx is not None:
                user = df_users.iloc[selected_user_idx]

                col1, col2, col3 = st.columns(3)

                with col1:
                    new_status = "Inactivo" if user['Activo'] else "Activo"
                    if st.button(f"🔄 {new_status}"):
                        if admin_db_manager.toggle_user_status(user['ID']):
                            st.success(f"Usuario marcado como {new_status.lower()}")
                            st.rerun()
                        else:
                            st.error("Error al cambiar estado")

                with col2:
                    if st.button("📧 Enviar Email"):
                        show_send_email_form(user)

                with col3:
                    if st.button("📊 Ver Historial"):
                        show_user_history(user['ID'])

        # Mostrar tabla de usuarios
        st.dataframe(df_users, use_container_width=True)
    else:
        st.info("No hay usuarios registrados")


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

    # Sección para agregar créditos
    st.subheader("➕ Agregar Créditos a Usuario")

    with st.form("add_credits_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            user_email = st.text_input("Email del usuario:")

        with col2:
            credits_amount = st.number_input("Cantidad de créditos:", min_value=1, max_value=100, value=1)

        with col3:
            reason = st.text_input("Motivo:", placeholder="Ej: Promoción mensual")

        if st.form_submit_button("💰 Agregar Créditos", type="primary"):
            if user_email and credits_amount:
                admin_user = st.session_state.get('admin_user', {})
                success = admin_db_manager.add_credits_to_user(
                    user_email,
                    credits_amount,
                    reason or "Créditos agregados por administrador",
                    admin_user.get('username', 'admin')
                )

                if success:
                    st.success(f"✅ {credits_amount} créditos agregados a {user_email}")
                    # Enviar email de notificación
                    send_credits_notification_email(user_email, credits_amount, reason)
                    st.rerun()
                else:
                    st.error("❌ Error: Usuario no encontrado o error en la base de datos")
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


def send_credits_notification_email(user_email, credits_amount, reason):
    """Enviar notificación de créditos agregados"""
    try:
        if email_manager.is_configured():
            # Implementar notificación de créditos
            pass
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