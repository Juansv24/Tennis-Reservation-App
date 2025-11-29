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


    # Mostrar mensaje de éxito de inicio de sesión automático
    if st.session_state.get('show_auto_login_notice', False):
        st.success("✅ **Sesión iniciada automáticamente** - ¡Tu sesión fue restaurada!")
        st.session_state.show_auto_login_notice = False

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
        # Sanitize error message to handle unicode encoding issues
        try:
            error_msg = str(e)
        except UnicodeEncodeError:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
        st.error(f"Error en la aplicación: {error_msg}")
        st.info("Intenta actualizar la página o contacta al administrador.")

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
        st.error("Error Critico de la Aplicacion")
        st.exception(e)

        if st.button("🔄 Reiniciar Aplicación"):
            # Limpiar estado de sesión problemático
            for key in list(st.session_state.keys()):
                if key not in ['session_token', 'authenticated', 'user_info']:
                    del st.session_state[key]
            st.rerun()

def check_system_health():
    """Verificar salud del sistema - LIGHTWEIGHT version para no bloquear startup

    FIX #2: Reemplazado verificación pesada por simple query con limit
    Esto reduce de ~10 DB calls a 2 lightweight queries bajo concurrencia
    """
    try:
        # FIX #2a: Reemplazar get_all_reservations() (full table scan) con simple limit query
        # Esto evita traer TODOS los registros de la tabla
        db_manager.client.table('reservations').select('id').limit(1).execute()

        from auth_manager import auth_manager
        # Verificación ligera - solo verificar que la tabla existe
        auth_manager.client.table('users').select('id').limit(1).execute()

        return True, "Sistema operacional"

    except Exception as e:
        # FIX #2b: Log pero no bloquear - la app debería cargar incluso si health check falla
        print(f"[WARNING] Health check warning: {str(e)}")
        return False, f"Health check: {str(e)}"

if __name__ == "__main__":
    # FIX #2c: No bloquear en health check - mostrar warning pero dejar que app cargue
    is_healthy, health_message = check_system_health()

    try:
        main()
    except Exception as e:
        # Si health check falló previamente, mostrar warning + error app
        if not is_healthy:
            st.warning(f"Health check warning: {health_message}")
        st.error("Error en la aplicacion")
        st.exception(e)
        if st.button("🔄 Reintentar"):
            st.rerun()