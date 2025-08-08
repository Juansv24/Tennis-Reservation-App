"""
Pestaña de Administración para Sistema de Reservas de Cancha de Tenis
Maneja la interfaz de administración
"""

import streamlit as st
import datetime
from datetime import timedelta
import pandas as pd
from database_manager import db_manager
from timezone_utils import get_colombia_today, get_colombia_now

# Configuración de administración
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "tennis123"

def format_hour(hour: int) -> str:
    """Formatear hora para mostrar"""
    return f"{hour:02d}:00"

def format_date(date_str: str) -> str:
    """Formatear fecha en español"""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

        day_name = days[date_obj.weekday()]
        month_name = months[date_obj.month - 1]

        return f"{day_name}, {date_obj.day} de {month_name} de {date_obj.year}"
    except:
        return date_str

def show_admin_tab():
    """Mostrar la pestaña de administración"""
    if not st.session_state.get('admin_logged_in', False):
        show_admin_login()
    else:
        show_admin_dashboard()

def show_admin_login():
    """Mostrar interfaz de login de administrador"""
    st.header("🔐 Acceso de Administrador")

    # Centrar el formulario
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.container():
            st.markdown("### 👤 Iniciar Sesión")

            with st.form("admin_login", clear_on_submit=False):
                username = st.text_input(
                    "👤 Usuario",
                    placeholder="Ingresa tu usuario",
                    help="Usuario administrador del sistema"
                )

                password = st.text_input(
                    "🔑 Contraseña",
                    type="password",
                    placeholder="Ingresa tu contraseña",
                    help="Contraseña del administrador"
                )

                # Botón de login
                login_button = st.form_submit_button(
                    "🚪 Iniciar Sesión",
                    use_container_width=True,
                    type="primary"
                )

                if login_button:
                    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                        st.session_state.admin_logged_in = True
                        st.success("✅ Acceso concedido")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
                        if username and password:  # Solo mostrar si se ingresaron datos
                            st.warning("⚠️ Verifica tu usuario y contraseña")

            # Mostrar credenciales para demo (remover en producción)
            with st.expander("💡 Credenciales de prueba", expanded=False):
                st.info(f"""
                **Para fines de demostración:**
                
                👤 **Usuario:** `{ADMIN_USERNAME}`
                
                🔑 **Contraseña:** `{ADMIN_PASSWORD}`
                """)
                st.caption("⚠️ En producción, estas credenciales no se mostrarían.")

def show_admin_dashboard():
    """Mostrar el panel de administración"""
    st.header("⚙️ Panel de Administración")

    # Barra superior con información del admin y logout
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.markdown(f"👋 **Bienvenido, {ADMIN_USERNAME}**")

    with col2:
        current_time = get_colombia_now()
        st.caption(f"🕐 {current_time.strftime('%d/%m/%Y %H:%M:%S')}")

    with col3:
        if st.button("🚪 Cerrar Sesión", type="secondary"):
            st.session_state.admin_logged_in = False
            # Limpiar otros estados de admin si existen
            for key in list(st.session_state.keys()):
                if key.startswith('admin_'):
                    del st.session_state[key]
            st.rerun()

    st.divider()

    # Pestañas del panel de administración
    admin_tabs = st.tabs([
        "📋 Gestión de Reservas",
        "📊 Panel & Estadísticas",
        "⚙️ Configuración del Sistema",
        "🔧 Mantenimiento"
    ])

    with admin_tabs[0]:
        show_reservations_management()

    with admin_tabs[1]:
        show_statistics_dashboard()

    with admin_tabs[2]:
        show_configuration_panel()

    with admin_tabs[3]:
        show_maintenance_panel()

