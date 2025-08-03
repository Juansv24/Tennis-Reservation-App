"""
Aplicación Principal Mejorada para Sistema de Reservas de Cancha de Tenis con Autenticación Funcional
"""

import streamlit as st
import datetime
from reservations_tab import show_reservation_tab, init_reservation_session_state
from auth_interface import show_auth_interface
from auth_utils import (
    init_auth_session_state,
    require_authentication,
    get_current_user,
    try_auto_login
)
from database_manager import db_manager

# Colores US Open
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"

def setup_page_config():
    """Configurar la página de Streamlit"""
    st.set_page_config(
        page_title="Reservas de Cancha de Tenis",
        page_icon="🎾",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def init_session_state():
    """Inicializar estado de sesión - ¡AUTENTICACIÓN PRIMERO!"""
    # CRÍTICO: Inicializar estados de autenticación PRIMERO, antes de cualquier UI
    init_auth_session_state()

    # Luego inicializar otros estados
    init_reservation_session_state()

    # Estado global de la aplicación
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True

def show_header():
    """Mostrar el encabezado principal"""
    user_info = get_current_user()

    st.markdown("---")

    # Sección de título
    col1, col2, col3 = st.columns([1, 20, 1])

    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #001854 0%, #2478CC 100%); border-radius: 10px; color: white; margin-bottom: 20px;'>
            <h1 style='margin: 0; color: white;'>🎾 Reservas de Cancha de Tenis</h1>
            <p style='margin: 10px 0 0 0; color: white;'>Cancha Pública Colina Campestre</p>
        </div>
        """, unsafe_allow_html=True)

    # Saludo al usuario
    if user_info:
        st.success(f"¡Bienvenido de vuelta, **{user_info['full_name']}**! 👋")

        # Mostrar información de sesión
        session_token = user_info.get('session_token', '')
        if session_token:
            st.info("🔐 Tu sesión está activa y recordada")

    # Mostrar mensaje de éxito de inicio de sesión automático
    if st.session_state.get('show_auto_login_notice', False):
        st.success("✅ **Sesión iniciada automáticamente** - ¡Tu sesión fue restaurada!")
        st.session_state.show_auto_login_notice = False

    st.markdown("---")

def show_footer():
    """Mostrar pie de página"""
    st.markdown("---")

    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

    with footer_col2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666;'>
                <b>Sistema de Reservas de Cancha de Tenis</b><br>
                Desarrollada en Streamlit por Juan Sebastian Vallejo
            </div>
            """,
            unsafe_allow_html=True
        )

def show_main_content():
    """Mostrar contenido principal de la aplicación"""

    # Verificar autenticación (esto intentará automáticamente el inicio de sesión automático)
    if not require_authentication():
        # Mostrar interfaz de inicio de sesión
        show_auth_interface()
        return

    # Usuario está autenticado - mostrar contenido principal
    try:
        show_reservation_tab()

    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")
        st.info("🔄 Intenta actualizar la página o contacta al administrador.")

        # Mostrar detalles del error
        with st.expander("🔧 Detalles del Error"):
            st.exception(e)

def main():
    """Función principal de la aplicación"""
    try:
        # PASO 1: Configurar página
        setup_page_config()

        # PASO 2: Inicializar estado de sesión (incluye intento de inicio de sesión automático)
        init_session_state()

        # PASO 3: Mostrar encabezado
        show_header()

        # PASO 4: Mostrar contenido principal
        show_main_content()

        # PASO 5: Mostrar pie de página
        show_footer()

    except Exception as e:
        st.error("🚨 Error Crítico de la Aplicación")
        st.exception(e)

        if st.button("🔄 Reiniciar Aplicación"):
            # Limpiar estado de sesión problemático
            for key in list(st.session_state.keys()):
                if key not in ['session_token', 'authenticated', 'user_info']:
                    del st.session_state[key]
            st.rerun()

def check_system_health():
    """Verificar salud del sistema"""
    try:
        # Probar base de datos
        db_manager.get_all_reservations()

        # Probar sistema de autenticación
        from auth_manager import auth_manager
        auth_manager.init_auth_tables()

        return True, "Sistema operacional"

    except Exception as e:
        return False, f"Error del sistema: {str(e)}"

if __name__ == "__main__":
    # Verificar salud del sistema
    is_healthy, health_message = check_system_health()

    if is_healthy:
        main()
    else:
        st.error(f"🚨 Falló la Verificación de Salud del Sistema: {health_message}")
        if st.button("🔄 Reintentar"):
            st.rerun()