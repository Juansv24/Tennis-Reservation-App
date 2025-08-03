"""
Enhanced Authentication Utilities for Tennis Court Reservation System
Added persistent session management with browser storage fallback
"""

import streamlit as st
from auth_manager import auth_manager

def get_session_token_key():
    """Get a unique key for storing session token"""
    return "tennis_app_session_token"

def save_session_token(token: str):
    """Save session token securely"""
    # Store in session state as primary method
    st.session_state.session_token = token

    # Also try to use query params as fallback for persistence
    try:
        if 'session_token' not in st.query_params:
            st.query_params.session_token = token
    except:
        pass  # Ignore if query params aren't available

def get_saved_session_token():
    """Retrieve saved session token"""
    # First check session state
    if hasattr(st.session_state, 'session_token') and st.session_state.session_token:
        return st.session_state.session_token

    # Then check query params
    try:
        if 'session_token' in st.query_params:
            return st.query_params.session_token
    except:
        pass

    return None

def clear_session_token():
    """Clear saved session token"""
    # Clear from session state
    if hasattr(st.session_state, 'session_token'):
        st.session_state.session_token = None

    # Clear from query params
    try:
        if 'session_token' in st.query_params:
            del st.query_params.session_token
    except:
        pass

def try_auto_login():
    """
    Attempt automatic login using saved session token

    Returns:
        bool: True if auto-login successful
    """
    # Skip if already authenticated
    if st.session_state.get('authenticated', False):
        return True

    # Get saved session token
    session_token = get_saved_session_token()

    if not session_token:
        return False

    # Validate session with the server
    user_info = auth_manager.validate_session(session_token)

    if user_info:
        # Session is valid, restore authentication state
        st.session_state.authenticated = True
        st.session_state.user_info = user_info
        save_session_token(session_token)  # Ensure it's saved
        return True
    else:
        # Session is invalid, clear it
        clear_session_token()
        return False

def require_authentication():
    """
    Enhanced authentication check with auto-login

    Returns:
        bool: True si el usuario está autenticado
    """
    # Try auto-login first
    if try_auto_login():
        return True

    # Check current session state
    if not st.session_state.get('authenticated', False):
        return False

    # Verify user info exists
    user_info = st.session_state.get('user_info')
    if not user_info:
        logout_user()
        return False

    # Verify session token is still valid
    session_token = user_info.get('session_token')
    if session_token:
        # Validate token with server
        updated_user_info = auth_manager.validate_session(session_token)
        if not updated_user_info:
            logout_user()
            return False

        # Update user info if needed
        st.session_state.user_info = updated_user_info

    return True

def get_current_user():
    """
    Obtener información del usuario actual

    Returns:
        Dict or None: Información del usuario si está autenticado
    """
    if require_authentication():
        return st.session_state.user_info
    return None

def logout_user():
    """Cerrar sesión del usuario y limpiar tokens"""
    # Get session token before clearing state
    session_token = None
    if hasattr(st.session_state, 'user_info') and st.session_state.user_info:
        session_token = st.session_state.user_info.get('session_token')

    # Destroy session on server
    if session_token:
        auth_manager.destroy_session(session_token)

    # Clear local session data
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.auth_mode = 'login'

    # Clear session token
    clear_session_token()

    # Limpiar otros estados de sesión relacionados con reservas
    if 'selected_hours' in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' in st.session_state:
        st.session_state.selected_date = None

    st.success("✅ You have been signed out successfully")
    st.rerun()

def logout_all_sessions():
    """Cerrar todas las sesiones del usuario en todos los dispositivos"""
    user_info = get_current_user()
    if user_info:
        auth_manager.destroy_all_user_sessions(user_info['id'])
        logout_user()

def init_auth_session_state():
    """Inicializar estado de sesión de autenticación"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'  # 'login' o 'register'

    # Try auto-login on initialization
    try_auto_login()