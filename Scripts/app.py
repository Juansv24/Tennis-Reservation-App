"""
Enhanced Main Application for Tennis Court Reservation System with Persistent Authentication
Coordinates all components and manages the main interface with session persistence
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

# US Open colors
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"

def setup_page_config():
    """Configurar la página de Streamlit"""
    st.set_page_config(
        page_title="Tennis Court Reservations",
        page_icon="🎾",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def init_session_state():
    """Inicializar el estado de sesión global"""
    # Inicializar estados de autenticación primero (incluye auto-login)
    init_auth_session_state()
    
    # Inicializar estados específicos de cada pestaña
    init_reservation_session_state()
    
    # Estado global de la aplicación
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True

def show_header():
    """Mostrar el encabezado principal de la aplicación"""
    # Obtener información del usuario actual
    user_info = get_current_user()
    
    # Simple header using Streamlit components instead of complex HTML
    st.markdown("---")
    
    # Title and subtitle
    col1, col2, col3 = st.columns([1, 20, 1])
    
    with col2:
        # Load and display the tennis ball image with title
        try:
            # Display image and title in the same line
            st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #001854 0%, #2478CC 100%); border-radius: 10px; color: white; margin-bottom: 20px;'>
                <div style='display: flex; align-items: center; justify-content: center; gap: 15px;'>
                    <img src="data:image/png;base64,{}" style='width: 60px; height: 60px;'>
                    <h1 style='margin: 0; color: white;'>Reservas Cancha de Tenis Colina Campestre </h1>
                </div>
            </div>
            """.format(get_tennis_ball_base64()), unsafe_allow_html=True)
        except:
            # Fallback to emoji if image fails to load
            st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #001854 0%, #2478CC 100%); border-radius: 10px; color: white; margin-bottom: 20px;'>
                <h1 style='margin: 0; color: white;'>🎾 Tennis Court Reservations</h1>
                <p style='margin: 10px 0 0 0; color: white;'>Cancha Pública Colina Campestre</p>
            </div>
            """, unsafe_allow_html=True)
    
    # User greeting if logged in
    if user_info:
        st.success(f"Welcome back, **{user_info['full_name']}**! 👋")
        
        # Show session indicator
        session_token = user_info.get('session_token', '')
        if session_token:
            st.info("🔐 Your session is securely maintained")
    
    # Show auto-login notice if it happened
    if st.session_state.get('show_auto_login_notice', False):
        st.success("✅ **Automatically signed in** - Your session was restored from your last visit")
        st.session_state.show_auto_login_notice = False
    
    st.markdown("---")

def get_tennis_ball_base64():
    """Convert tennis ball PNG image to base64 string"""
    import base64
    
    # Try to read the tennis ball image
    try:
        with open("tennis_ball.png", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        # If file not found, try alternative paths
        try:
            with open("assets/tennis_ball.png", "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            # If still not found, raise exception to use fallback
            raise Exception("Tennis ball image not found")

def show_footer():
    """Mostrar pie de página mejorado"""
    st.markdown("---")
    
    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
    
    with footer_col2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666;'>
                <b>Tennis Court Reservation System</b><br>
                Built with Streamlit • SQLite Database • Persistent Sessions<br>
                <small>🔒 Your session is securely maintained across visits</small>
            </div>
            """, 
            unsafe_allow_html=True
        )

def show_main_content():
    """Mostrar contenido principal de la aplicación con auto-login mejorado"""
    # Primero intentar auto-login silencioso
    auto_login_success = try_auto_login()
    
    # Si el auto-login fue exitoso, mostrar notificación
    if auto_login_success and st.session_state.get('authenticated', False):
        # Solo mostrar la notificación si es la primera vez en esta sesión
        if not st.session_state.get('auto_login_notified', False):
            st.session_state.show_auto_login_notice = True
            st.session_state.auto_login_notified = True
    
    # Verificar autenticación
    if not require_authentication():
        # Mostrar interfaz de autenticación
        authenticated = show_auth_interface()
        if not authenticated:
            return
    
    # Usuario autenticado - mostrar contenido principal
    try:
        show_reservation_tab()
    
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")
        st.info("🔄 Intenta recargar la página o contacta al administrador.")
        
        # Mostrar detalles del error en un expander
        with st.expander("🔧 Detalles del Error"):
            st.exception(e)

def main():
    """Función principal de la aplicación"""
    # Configurar página
    setup_page_config()
    
    # Inicializar estado de sesión
    init_session_state()
    
    # Mostrar encabezado
    show_header()
    
    # Mostrar contenido principal
    show_main_content()
    
    # Mostrar pie de página
    show_footer()

def check_system_health():
    """Verificar la salud del sistema"""
    try:
        # Verificar conexión a base de datos
        db_manager.get_all_reservations()
        
        # Verificar tablas de autenticación
        from auth_manager import auth_manager
        auth_manager.init_auth_tables()
        
        return True, "Sistema operativo"
    
    except Exception as e:
        return False, f"Error del sistema: {str(e)}"


if __name__ == "__main__":
    # Verificar salud del sistema antes de iniciar
    is_healthy, health_message = check_system_health()
    
    if is_healthy:
        main()
