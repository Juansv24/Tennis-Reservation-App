
"""
Working Authentication Utilities for Streamlit Cloud
Uses URL query parameters as the primary persistence method
"""

import streamlit as st
from auth_manager import auth_manager
import time

def save_session_token(token: str):
    """Save session token using URL query parameters"""
    # Store in session state for current session
    st.session_state.session_token = token
    st.session_state.token_saved_at = time.time()
    
    # Save in URL for persistence across refreshes
    try:
        st.query_params["session_token"] = token
    except Exception as e:
        st.warning(f"Could not save session: {e}")

def get_saved_session_token():
    """Get saved session token from session state or URL"""
    
    # First try session state (current session)
    if (hasattr(st.session_state, 'session_token') and 
        st.session_state.session_token):
        return st.session_state.session_token
    
    # Then try URL query params (for refreshes/new tabs)
    try:
        if "session_token" in st.query_params:
            token = st.query_params["session_token"]
            if token:
                # Restore to session state
                st.session_state.session_token = token
                st.session_state.token_saved_at = time.time()
                return token
    except Exception:
        pass
    
    return None

def clear_session_token():
    """Clear session token from all sources"""
    # Clear session state
    if hasattr(st.session_state, 'session_token'):
        st.session_state.session_token = None
    if hasattr(st.session_state, 'token_saved_at'):
        st.session_state.token_saved_at = None
    
    # Clear URL params
    try:
        if "session_token" in st.query_params:
            del st.query_params["session_token"]
    except Exception:
        pass

def try_auto_login():
    """Attempt automatic login using saved session token"""
    
    # Skip if already authenticated
    if st.session_state.get('authenticated', False):
        return True
    
    # Get saved token
    session_token = get_saved_session_token()
    
    if not session_token:
        return False
    
    try:
        # Validate session with server
        user_info = auth_manager.validate_session(session_token)
        
        if user_info:
            # Valid session - restore authentication
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            
            # Ensure token is properly saved
            save_session_token(session_token)
            
            return True
        else:
            # Invalid session - clean up
            clear_session_token()
            return False
            
    except Exception as e:
        # Error during validation - clean up
        clear_session_token()
        return False

def require_authentication():
    """Check authentication with auto-login"""
    # Always try auto-login first - this is the key fix
    return try_auto_login()

def get_current_user():
    """Get current user information"""
    if require_authentication():
        return st.session_state.user_info
    return None

def logout_user():
    """Logout user and clean up all session data"""
    
    # Get session token before clearing
    session_token = None
    if hasattr(st.session_state, 'user_info') and st.session_state.user_info:
        session_token = st.session_state.user_info.get('session_token')
    
    # Destroy server session
    if session_token:
        try:
            auth_manager.destroy_session(session_token)
        except Exception:
            pass  # Continue even if server cleanup fails
    
    # Clear authentication state
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.auth_mode = 'login'
    
    # Clear session tokens
    clear_session_token()
    
    # Clear reservation states
    reservation_keys = ['selected_hours', 'selected_date', 'show_auto_login_notice']
    for key in reservation_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("✅ You have been signed out successfully")
    st.rerun()

def logout_all_sessions():
    """Sign out from all devices"""
    user_info = get_current_user()
    if user_info:
        try:
            auth_manager.destroy_all_user_sessions(user_info['id'])
        except Exception:
            pass
        logout_user()


def init_auth_session_state():
    """Inicializar estado de sesión de autenticación"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'  # 'login' o 'register'

    # NEW: Add these email verification states
    if 'awaiting_verification' not in st.session_state:
        st.session_state.awaiting_verification = False
    if 'pending_name' not in st.session_state:
        st.session_state.pending_name = None
    if 'pending_email' not in st.session_state:
        st.session_state.pending_email = None
    if 'pending_password' not in st.session_state:
        st.session_state.pending_password = None

    # Try auto-login on initialization
    try_auto_login()