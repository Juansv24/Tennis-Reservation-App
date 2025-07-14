"""
Enhanced Authentication Utilities with Improved Session Persistence
Fixed for published Streamlit apps
"""

import streamlit as st
from auth_manager import auth_manager
import hashlib

def get_session_token_key():
    """Get a unique key for storing session token based on user's browser"""
    # Create a more stable key that persists across sessions
    try:
        # Use a combination of user agent and other stable browser info
        user_agent = st.context.headers.get("user-agent", "unknown")
        stable_key = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        return f"tennis_session_{stable_key}"
    except:
        return "tennis_app_session_token"

def save_session_token(token: str):
    """Save session token with multiple persistence methods"""
    # Method 1: Session state (primary for current session)
    st.session_state.session_token = token
    
    # Method 2: Use cookies via JavaScript if possible
    try:
        # Set a cookie that expires in 30 days
        cookie_script = f"""
        <script>
        document.cookie = "tennis_session_token={token}; max-age=2592000; path=/; SameSite=Lax";
        </script>
        """
        st.markdown(cookie_script, unsafe_allow_html=True)
    except:
        pass
    
    # Method 3: Browser storage via JavaScript
    try:
        storage_script = f"""
        <script>
        try {{
            localStorage.setItem('tennis_session_token', '{token}');
        }} catch(e) {{
            // Fallback to sessionStorage if localStorage fails
            try {{
                sessionStorage.setItem('tennis_session_token', '{token}');
            }} catch(e2) {{
                console.log('Storage not available');
            }}
        }}
        </script>
        """
        st.markdown(storage_script, unsafe_allow_html=True)
    except:
        pass

def get_saved_session_token():
    """Retrieve saved session token from multiple sources"""
    # Method 1: Check session state first
    if hasattr(st.session_state, 'session_token') and st.session_state.session_token:
        return st.session_state.session_token
    
    # Method 2: Check cookies
    try:
        cookies = st.context.cookies
        if 'tennis_session_token' in cookies:
            token = cookies['tennis_session_token']
            if token and len(token) > 10:  # Basic validation
                return token
    except:
        pass
    
    # Method 3: Try to get from browser storage via query params
    # (This is a workaround for published apps)
    try:
        if hasattr(st.session_state, 'browser_session_token'):
            return st.session_state.browser_session_token
    except:
        pass
    
    return None

def clear_session_token():
    """Clear saved session token from all sources"""
    # Clear from session state
    if hasattr(st.session_state, 'session_token'):
        st.session_state.session_token = None
    
    if hasattr(st.session_state, 'browser_session_token'):
        st.session_state.browser_session_token = None
    
    # Clear cookies via JavaScript
    try:
        clear_cookie_script = """
        <script>
        document.cookie = "tennis_session_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        </script>
        """
        st.markdown(clear_cookie_script, unsafe_allow_html=True)
    except:
        pass
    
    # Clear browser storage
    try:
        clear_storage_script = """
        <script>
        try {
            localStorage.removeItem('tennis_session_token');
            sessionStorage.removeItem('tennis_session_token');
        } catch(e) {
            console.log('Storage clear failed');
        }
        </script>
        """
        st.markdown(clear_storage_script, unsafe_allow_html=True)
    except:
        pass

def try_auto_login():
    """
    Enhanced automatic login with better error handling
    """
    # Skip if already authenticated
    if st.session_state.get('authenticated', False):
        return True
    
    # Get saved session token
    session_token = get_saved_session_token()
    
    if not session_token:
        return False
    
    try:
        # Validate session with the server
        user_info = auth_manager.validate_session(session_token)
        
        if user_info:
            # Session is valid, restore authentication state
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            save_session_token(session_token)  # Refresh the token storage
            return True
        else:
            # Session is invalid, clear it
            clear_session_token()
            return False
    except Exception as e:
        # If there's any error, clear the token and fail gracefully
        clear_session_token()
        return False

def handle_login(email: str, password: str, remember_me: bool = False):
    """Enhanced login handler with better session management"""
    if not email or not password:
        st.error("Please fill in all fields")
        return
    
    try:
        success, message, user_info = auth_manager.login_user(email, password, remember_me)
        
        if success:
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            
            # Enhanced session token saving for remember me
            if user_info and user_info.get('session_token'):
                save_session_token(user_info['session_token'])
                
                # Additional persistence for remember me
                if remember_me:
                    # Store additional identifier for long-term persistence
                    st.session_state.browser_session_token = user_info['session_token']
            
            duration_text = "30 days" if remember_me else "1 day"
            st.success(f"Welcome back, {user_info['full_name']}! Session valid for {duration_text}.")
            
            # Show persistence status
            if remember_me:
                st.info("🔒 Your session will be remembered across browser visits")
            
            st.balloons()
            st.rerun()
        else:
            st.error(message)
            
    except Exception as e:
        st.error("Login failed. Please try again.")

def init_auth_session_state():
    """Enhanced initialization with immediate auto-login attempt"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'
    
    # Enhanced auto-login attempt
    if not st.session_state.get('authenticated', False):
        try_auto_login()

# Additional function to show session management UI
def show_session_debug_info():
    """Debug function to show session info (remove in production)"""
    if st.session_state.get('authenticated', False):
        with st.expander("🔧 Session Debug Info"):
            st.write("Session State Token:", bool(st.session_state.get('session_token')))
            st.write("Browser Session Token:", bool(st.session_state.get('browser_session_token')))
            user_info = st.session_state.get('user_info', {})
            if user_info and 'session_token' in user_info:
                token = user_info['session_token']
                st.write("Current Token Preview:", f"{token[:8]}...{token[-4:]}" if len(token) > 12 else token)

# Additional persistence method for Streamlit Cloud
def ensure_session_persistence():
    """Call this in main app to ensure session persistence"""
    # Add a hidden component that helps with session persistence
    session_persistence_html = """
    <script>
    // Enhanced session persistence for Streamlit Cloud
    window.tennisSessionManager = {
        saveToken: function(token) {
            try {
                localStorage.setItem('tennis_session_token', token);
                document.cookie = "tennis_session_token=" + token + "; max-age=2592000; path=/; SameSite=Lax";
            } catch(e) {
                console.log('Session save failed:', e);
            }
        },
        
        getToken: function() {
            try {
                return localStorage.getItem('tennis_session_token') || 
                       document.cookie.split('; ').find(row => row.startsWith('tennis_session_token='))?.split('=')[1];
            } catch(e) {
                return null;
            }
        },
        
        clearToken: function() {
            try {
                localStorage.removeItem('tennis_session_token');
                document.cookie = "tennis_session_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            } catch(e) {
                console.log('Session clear failed:', e);
            }
        }
    };
    </script>
    """
    st.markdown(session_persistence_html, unsafe_allow_html=True)