"""
Enhanced Main Application for Tennis Court Reservation System with Working Authentication
The key fix: Initialize auth state BEFORE any other UI components
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
    """Configure the Streamlit page"""
    st.set_page_config(
        page_title="Tennis Court Reservations",
        page_icon="🎾",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def init_session_state():
    """Initialize session state - AUTH FIRST!"""
    # CRITICAL: Initialize auth states FIRST, before any UI
    init_auth_session_state()
    
    # Then initialize other states
    init_reservation_session_state()
    
    # Global app state
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True

def show_header():
    """Show the main header"""
    user_info = get_current_user()
    
    st.markdown("---")
    
    # Title section
    col1, col2, col3 = st.columns([1, 20, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #001854 0%, #2478CC 100%); border-radius: 10px; color: white; margin-bottom: 20px;'>
            <h1 style='margin: 0; color: white;'>🎾 Tennis Court Reservations</h1>
            <p style='margin: 10px 0 0 0; color: white;'>Cancha Pública Colina Campestre</p>
        </div>
        """, unsafe_allow_html=True)
    
    # User greeting
    if user_info:
        st.success(f"Welcome back, **{user_info['full_name']}**! 👋")
        
        # Show session info
        session_token = user_info.get('session_token', '')
        if session_token:
            st.info("🔐 Your session is active and remembered")
    
    # Show auto-login success message
    if st.session_state.get('show_auto_login_notice', False):
        st.success("✅ **Automatically signed in** - Your session was restored!")
        st.session_state.show_auto_login_notice = False
    
    st.markdown("---")

def show_footer():
    """Show footer"""
    st.markdown("---")
    
    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
    
    with footer_col2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666;'>
                <b>Tennis Court Reservation System</b><br>
                Built with Streamlit • SQLite Database • Persistent Sessions<br>
                <small>🔒 Your session is automatically saved and restored</small>
            </div>
            """, 
            unsafe_allow_html=True
        )

def show_main_content():
    """Show main application content"""
    
    # Check authentication (this will automatically try auto-login)
    if not require_authentication():
        # Show login interface
        show_auth_interface()
        return
    
    # User is authenticated - show main content
    try:
        show_reservation_tab()
    
    except Exception as e:
        st.error(f"❌ Error in the application: {str(e)}")
        st.info("🔄 Try refreshing the page or contact the administrator.")
        
        # Show error details
        with st.expander("🔧 Error Details"):
            st.exception(e)

def main():
    """Main application function"""
    try:
        # STEP 1: Configure page
        setup_page_config()
        
        # STEP 2: Initialize session state (includes auto-login attempt)
        init_session_state()
        
        # STEP 3: Show header
        show_header()
        
        # STEP 4: Show main content
        show_main_content()
        
        # STEP 5: Show footer
        show_footer()
        
    except Exception as e:
        st.error("🚨 Critical Application Error")
        st.exception(e)
        
        if st.button("🔄 Reset Application"):
            # Clear problematic session state
            for key in list(st.session_state.keys()):
                if key not in ['session_token', 'authenticated', 'user_info']:
                    del st.session_state[key]
            st.rerun()

def check_system_health():
    """Check system health"""
    try:
        # Test database
        db_manager.get_all_reservations()
        
        # Test auth system
        from auth_manager import auth_manager
        auth_manager.init_auth_tables()
        
        return True, "System operational"
    
    except Exception as e:
        return False, f"System error: {str(e)}"

if __name__ == "__main__":
    # Check system health
    is_healthy, health_message = check_system_health()
    
    if is_healthy:
        main()
    else:
        st.error(f"🚨 System Health Check Failed: {health_message}")
        if st.button("🔄 Retry"):
            st.rerun()