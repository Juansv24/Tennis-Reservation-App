"""
Simplified Authentication Utilities for Tennis Court Reservation System
Removed persistent session management - sessions only last for browser session
"""

import streamlit as st
from auth_manager import auth_manager


def require_authentication():
    """
    Simple authentication check without auto-login

    Returns:
        bool: True if user is authenticated
    """
    # Check current session state
    if not st.session_state.get('authenticated', False):
        return False

    # Verify user info exists
    user_info = st.session_state.get('user_info')
    if not user_info:
        logout_user()
        return False

    return True


def get_current_user():
    """
    Get current user information

    Returns:
        Dict or None: User information if authenticated
    """
    if require_authentication():
        return st.session_state.user_info
    return None


def logout_user():
    """Log out user and clear session data"""
    # Clear local session data
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.auth_mode = 'login'

    # Clear other reservation-related session states
    if 'selected_hours' in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' in st.session_state:
        st.session_state.selected_date = None

    st.success("✅ You have been signed out successfully")
    st.rerun()


def logout_all_sessions():
    """Simple logout - same as regular logout without persistent sessions"""
    logout_user()


def init_auth_session_state():
    """Initialize authentication session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'  # 'login' or 'register'