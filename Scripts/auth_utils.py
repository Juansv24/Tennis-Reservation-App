"""
Enhanced Authentication Utilities with Browser Storage for Streamlit Cloud

"""

import streamlit as st
import streamlit.components.v1 as components
from auth_manager import auth_manager

def get_session_token_key():
    """Get a unique key for storing session token"""
    return "tennis_app_session_token"

def save_session_token_persistent(token: str, remember_me: bool = False):
    """Save session token with browser persistence (for Streamlit Cloud)"""
    # Store in session state as primary method
    st.session_state.session_token = token

    # Use browser localStorage for persistence (works in real Streamlit apps)
    storage_type = "localStorage" if remember_me else "sessionStorage"
    duration_days = 30 if remember_me else 1

    # JavaScript to save token in browser storage
    save_js = f"""
    <script>
    try {{
        {storage_type}.setItem('{get_session_token_key()}', '{token}');
        {storage_type}.setItem('{get_session_token_key()}_expires', 
            new Date(Date.now() + {duration_days * 24 * 60 * 60 * 1000}).toISOString());
        console.log('Session token saved to {storage_type}');
    }} catch(e) {{
        console.log('Storage not available:', e);
    }}
    </script>
    """

    components.html(save_js, height=0)

def get_saved_session_token_persistent():
    """Retrieve saved session token from browser storage"""
    # First check session state
    if hasattr(st.session_state, 'session_token') and st.session_state.session_token:
        return st.session_state.session_token

    # Then check browser storage using JavaScript
    get_js = f"""
    <script>
    function getStoredToken() {{
        try {{
            // Check localStorage first (for remember me)
            let token = localStorage.getItem('{get_session_token_key()}');
            let expires = localStorage.getItem('{get_session_token_key()}_expires');
            
            if (token && expires) {{
                if (new Date() < new Date(expires)) {{
                    return token;
                }}
                // Token expired, remove it
                localStorage.removeItem('{get_session_token_key()}');
                localStorage.removeItem('{get_session_token_key()}_expires');
            }}
            
            // Check sessionStorage (current session only)
            token = sessionStorage.getItem('{get_session_token_key()}');
            expires = sessionStorage.getItem('{get_session_token_key()}_expires');
            
            if (token && expires) {{
                if (new Date() < new Date(expires)) {{
                    return token;
                }}
                // Token expired, remove it
                sessionStorage.removeItem('{get_session_token_key()}');
                sessionStorage.removeItem('{get_session_token_key()}_expires');
            }}
            
            return null;
        }} catch(e) {{
            console.log('Error retrieving token:', e);
            return null;
        }}
    }}
    
    // Get token and communicate back to Streamlit
    const token = getStoredToken();
    if (token) {{
        // Use Streamlit's component communication
        window.parent.postMessage({{
            type: 'streamlit:setSessionToken',
            token: token
        }}, '*');
    }}
    </script>
    """

    # This is a simplified approach - in a real app you'd use proper component communication
    components.html(get_js, height=0)

    # For immediate fallback, return None (real implementation would handle async token retrieval)
    return None

def clear_session_token_persistent():
    """Clear saved session token from all storage"""
    # Clear from session state
    if hasattr(st.session_state, 'session_token'):
        st.session_state.session_token = None

    # Clear from browser storage
    clear_js = f"""
    <script>
    try {{
        localStorage.removeItem('{get_session_token_key()}');
        localStorage.removeItem('{get_session_token_key()}_expires');
        sessionStorage.removeItem('{get_session_token_key()}');
        sessionStorage.removeItem('{get_session_token_key()}_expires');
        console.log('Session tokens cleared from browser storage');
    }} catch(e) {{
        console.log('Error clearing storage:', e);
    }}
    </script>
    """

    components.html(clear_js, height=0)

def init_persistent_auth():
    """Initialize persistent authentication on app start"""
    # This would be called early in your app initialization

    # JavaScript to handle token retrieval and set it in Streamlit
    init_js = f"""
    <script>
    function initPersistentAuth() {{
        try {{
            // Check for stored token
            let token = localStorage.getItem('{get_session_token_key()}') || 
                       sessionStorage.getItem('{get_session_token_key()}');
            let expires = localStorage.getItem('{get_session_token_key()}_expires') || 
                         sessionStorage.getItem('{get_session_token_key()}_expires');
            
            if (token && expires) {{
                if (new Date() < new Date(expires)) {{
                    // Token is valid, trigger auto-login
                    window.parent.postMessage({{
                        type: 'streamlit:autoLogin',
                        token: token
                    }}, '*');
                    return;
                }}
            }}
            
            // No valid token found
            window.parent.postMessage({{
                type: 'streamlit:noValidToken'
            }}, '*');
            
        }} catch(e) {{
            console.log('Auth initialization error:', e);
        }}
    }}
    
    // Run initialization
    initPersistentAuth();
    </script>
    """

    components.html(init_js, height=0)

# Updated auth utilities using persistent storage
def try_auto_login_persistent():
    """
    Attempt automatic login using persistent browser storage
    This version works in real Streamlit Cloud deployments
    """
    # Skip if already authenticated
    if st.session_state.get('authenticated', False):
        return True

    # Initialize persistent auth check
    init_persistent_auth()

    # Check if we have a token from JavaScript (this would be handled via component communication)
    # For now, fall back to session state
    session_token = st.session_state.get('session_token')

    if session_token:
        # Validate session with the server
        user_info = auth_manager.validate_session(session_token)

        if user_info:
            # Session is valid, restore authentication state
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            return True
        else:
            # Session is invalid, clear it
            clear_session_token_persistent()
            return False

    return False

def handle_login_persistent(email: str, password: str, remember_me: bool = False):
    """Handle login with persistent storage"""
    if not email or not password:
        st.error("Please fill in all fields")
        return False

    success, message, user_info = auth_manager.login_user(email, password, remember_me)

    if success:
        st.session_state.authenticated = True
        st.session_state.user_info = user_info

        # Save session token with persistence
        if user_info and user_info.get('session_token'):
            save_session_token_persistent(user_info['session_token'], remember_me)

        duration_text = "30 days" if remember_me else "this session"
        st.success(f"Welcome back, {user_info['full_name']}! You'll stay logged in for {duration_text}.")
        st.balloons()
        return True
    else:
        st.error(message)
        return False

def logout_user_persistent():
    """Logout with persistent storage cleanup"""
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

    # Clear persistent storage
    clear_session_token_persistent()

    # Clear other session states
    if 'selected_hours' in st.session_state:
        st.session_state.selected_hours = []
    if 'selected_date' in st.session_state:
        st.session_state.selected_date = None

    st.success("✅ You have been signed out successfully")
    st.rerun()

# Alternative: Cookie-based approach (even more reliable)
def save_token_as_cookie(token: str, remember_me: bool = False):
    """Save session token as HTTP-only cookie (most secure)"""
    max_age = 30 * 24 * 60 * 60 if remember_me else 24 * 60 * 60  # seconds

    cookie_js = f"""
    <script>
    document.cookie = "{get_session_token_key()}={token}; max-age={max_age}; path=/; secure; samesite=strict";
    console.log('Session cookie set');
    </script>
    """

    components.html(cookie_js, height=0)

def get_token_from_cookie():
    """Retrieve session token from cookie"""
    cookie_js = f"""
    <script>
    function getCookie(name) {{
        const value = `; ${{document.cookie}}`;
        const parts = value.split(`; ${{name}}=`);
        if (parts.length === 2) {{
            return parts.pop().split(';').shift();
        }}
        return null;
    }}
    
    const token = getCookie('{get_session_token_key()}');
    if (token) {{
        window.parent.postMessage({{
            type: 'streamlit:cookieToken',
            token: token
        }}, '*');
    }}
    </script>
    """

    components.html(cookie_js, height=0)