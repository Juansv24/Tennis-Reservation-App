"""
Simplified Main Application for Tennis Court Reservation System
Removed persistent authentication functionality
"""

import streamlit as st
import datetime
from reservations_tab import show_reservation_tab, init_reservation_session_state
from auth_interface import show_auth_interface
from auth_utils import init_auth_session_state, require_authentication, get_current_user
from database_manager import db_manager

# US Open colors
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"

def setup_page_config():
    """Configure Streamlit page"""
    st.set_page_config(
        page_title="Tennis Court Reservations",
        page_icon="🎾",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def init_session_state():
    """Initialize global session state"""
    # Initialize authentication states (no auto-login)
    init_auth_session_state()

    # Initialize specific tab states
    init_reservation_session_state()

    # Global app state
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True

def show_header():
    """Show main application header"""
    # Get current user information
    user_info = get_current_user()

    # Simple header using Streamlit components
    st.markdown("---")

    # Title and subtitle
    col1, col2, col3 = st.columns([1, 20, 1])

    with col2:
        # Display image and title
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
    """Show improved footer"""
    st.markdown("---")

    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

    with footer_col2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666;'>
                <b>Tennis Court Reservation System</b><br>
                Built with Streamlit • SQLite Database • Session-based Authentication<br>
                <small>🔒 Your session lasts until you close your browser</small>
            </div>
            """,
            unsafe_allow_html=True
        )

def show_main_content():
    """Show main application content"""
    # Check authentication
    if not require_authentication():
        # Show authentication interface
        authenticated = show_auth_interface()
        if not authenticated:
            return

    # User authenticated - show main content
    try:
        show_reservation_tab()

    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.info("🔄 Try reloading the page or contact administrator.")

        # Show error details in expander
        with st.expander("🔧 Error Details"):
            st.exception(e)

def main():
    """Main application function"""
    # Configure page
    setup_page_config()

    # Initialize session state
    init_session_state()

    # Show header
    show_header()

    # Show main content
    show_main_content()

    # Show footer
    show_footer()

def check_system_health():
    """Check system health"""
    try:
        # Check database connection
        db_manager.get_all_reservations()

        # Check authentication tables
        from auth_manager import auth_manager
        auth_manager.init_auth_tables()

        return True, "System operational"

    except Exception as e:
        return False, f"System error: {str(e)}"


if __name__ == "__main__":
    # Check system health before starting
    is_healthy, health_message = check_system_health()

    if is_healthy:
        main()
    else:
        st.error(f"🚨 System Health Check Failed: {health_message}")
        st.info("Please contact the administrator to resolve this issue.")