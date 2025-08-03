"""
Enhanced Authentication Interface for Tennis Court Reservation System
Added Remember Me functionality and improved session management
"""

import streamlit as st
from auth_manager import auth_manager
from auth_utils import logout_user, logout_all_sessions, init_auth_session_state, require_authentication, save_session_token
from email_config import email_manager
from database_manager import db_manager

# US Open colors
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"

def apply_auth_css():
    """Remove Streamlit's default form container styling"""
    st.markdown("""
    <style>
    /* Remove Streamlit's form container border and background */
    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        box-shadow: none !important;
    }
    
    /* Alternative selector in case the above doesn't work */
    .stForm {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        box-shadow: none !important;
    }
    
    /* Remove any form borders */
    form {
        border: none !important;
        background: transparent !important;
    }
    
    /* Target the specific form container */
    div[data-testid="stForm"] > div {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    
    /* Keep your other existing styles here if needed */
    .auth-header {
        text-align: center;
        color: #001854;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 30px;
        padding-bottom: 15px;
        border-bottom: 3px solid #FFD400;
    }
    </style>
    """, unsafe_allow_html=True)
    
def show_auth_interface():
    """Mostrar interfaz de autenticación"""
    apply_auth_css()
    
    # Verificar si el usuario ya está autenticado
    if st.session_state.get('authenticated', False):
        show_user_profile()
        return True
    
    # Header
    if st.session_state.auth_mode == 'login':
        st.markdown('<div class="auth-header">Welcome Back!</div>', unsafe_allow_html=True)
        show_login_form()
    else:
        st.markdown('<div class="auth-header">Join Us!</div>', unsafe_allow_html=True)
        show_registration_form()
    
    return False

def show_login_form():
    """Mostrar formulario de login con opción Remember Me"""
    st.markdown('<div class="auth-form">', unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("### Sign In")
        
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            key="login_email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        login_submitted = st.form_submit_button(
            "Sign In",
            type="primary",
            use_container_width=True
        )
        
        if login_submitted:
            handle_login(email, password, True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Switch to registration
    st.markdown(f"""
    <div class="switch-mode">
        <p>Don't have an account?</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Create New Account", key="switch_to_register", use_container_width=True):
        st.session_state.auth_mode = 'register'
        st.rerun()


def show_registration_form():
    """Mostrar formulario de registro con verificación por email"""
    st.markdown('<div class="auth-form">', unsafe_allow_html=True)

    # Check if we're in email verification step
    if st.session_state.get('awaiting_verification', False):
        show_email_verification_form()
    else:
        show_initial_registration_form()

    st.markdown('</div>', unsafe_allow_html=True)

    # Switch to login
    st.markdown(f"""
    <div class="switch-mode">
        <p>Already have an account?</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign In Instead", key="switch_to_login", use_container_width=True):
        st.session_state.auth_mode = 'login'
        st.session_state.awaiting_verification = False
        # Clear pending data when switching
        for key in ['pending_name', 'pending_email', 'pending_password']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def show_initial_registration_form():
    """Show initial registration form"""
    with st.form("registration_form"):
        st.markdown("### Create Account")

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name",
            key="register_name"
        )

        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            key="register_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a password (min. 6 characters)",
            key="register_password",
            help="Password must be at least 6 characters and contain letters and numbers"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password",
            key="register_confirm_password"
        )

        register_submitted = st.form_submit_button(
            "Send Verification Code",
            type="primary",
            use_container_width=True
        )

        if register_submitted:
            handle_initial_registration(full_name, email, password, confirm_password)


def show_email_verification_form():
    """Show email verification form"""
    st.success("📧 Verification code sent!")
    st.info(f"Please check your email: **{st.session_state.pending_email}**")

    with st.form("verification_form"):
        st.markdown("### Verify Your Email")

        verification_code = st.text_input(
            "Verification Code",
            placeholder="Enter 6-character code",
            max_chars=6,
            key="verification_code",
            help="Check your email for the verification code"
        ).upper()  # Convert to uppercase automatically

        col1, col2 = st.columns(2)

        with col1:
            verify_submitted = st.form_submit_button(
                "Verify & Create Account",
                type="primary",
                use_container_width=True
            )

        with col2:
            resend_submitted = st.form_submit_button(
                "Resend Code",
                use_container_width=True
            )

        if verify_submitted:
            handle_email_verification(verification_code)

        if resend_submitted:
            send_verification_code(st.session_state.pending_email, st.session_state.pending_name)

    # Option to go back and change email
    if st.button("← Change Email Address", key="change_email"):
        st.session_state.awaiting_verification = False
        st.rerun()


def handle_initial_registration(full_name: str, email: str, password: str, confirm_password: str):
    """Handle initial registration and send verification email"""
    # Basic validations
    if not all([full_name, email, password, confirm_password]):
        st.error("Please fill in all fields")
        return

    if password != confirm_password:
        st.error("Passwords do not match")
        return

    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        st.error("Please enter a valid email address")
        return

    # REPLACE THIS ENTIRE SECTION:
    # Check if email already exists
    try:
        # Use the auth_manager method instead of direct database access
        from auth_manager import auth_manager

        # Try to get user by email - this is safer than direct DB access
        with auth_manager.get_connection() as conn:
            cursor = conn.cursor()
            # Make sure users table exists first
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS users
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               email
                               TEXT
                               UNIQUE
                               NOT
                               NULL,
                               password_hash
                               TEXT
                               NOT
                               NULL,
                               salt
                               TEXT
                               NOT
                               NULL,
                               full_name
                               TEXT
                               NOT
                               NULL,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               last_login
                               TIMESTAMP,
                               is_active
                               BOOLEAN
                               DEFAULT
                               1
                           )
                           ''')

            cursor.execute('SELECT id FROM users WHERE email = ?', (email.strip().lower(),))
            if cursor.fetchone():
                st.error("An account with this email already exists")
                return

    except Exception as e:
        st.error(f"Error checking email availability: {str(e)}")
        # Don't return here - let them try anyway
        st.warning("Unable to verify email availability, but continuing with registration...")

    # Save pending registration data
    st.session_state.pending_name = full_name.strip()
    st.session_state.pending_email = email.strip().lower()
    st.session_state.pending_password = password

    # Send verification code
    if send_verification_code(email.strip().lower(), full_name.strip()):
        st.session_state.awaiting_verification = True
        st.rerun()


def send_verification_code(email: str, name: str) -> bool:
    """Send verification code to email"""
    try:
        # Check if email service is configured
        if not email_manager.is_configured():
            st.error("Email service is not configured. Please contact administrator.")
            return False

        # Generate code
        verification_code = email_manager.generate_verification_code()

        # Save to database
        if not db_manager.save_verification_code(email, verification_code):
            st.error("Error saving verification code. Please try again.")
            return False

        # Send email
        success, message = email_manager.send_verification_email(email, verification_code, name)

        if success:
            st.success("📧 Verification code sent to your email!")
            st.info("⏰ Code expires in 10 minutes")
            return True
        else:
            st.error(f"Failed to send email: {message}")
            return False

    except Exception as e:
        st.error(f"Error sending verification code: {str(e)}")
        return False


def handle_email_verification(verification_code: str):
    """Handle email verification"""
    if not verification_code:
        st.error("Please enter the verification code")
        return

    if len(verification_code) != 6:
        st.error("Verification code must be 6 characters")
        return

    # Attempt registration with verification
    success, message = auth_manager.register_user(
        st.session_state.pending_email,
        st.session_state.pending_password,
        st.session_state.pending_name,
        verification_code
    )

    if success:
        st.success("✅ " + message)
        st.info("You can now sign in with your new account!")

        # Clear pending data
        st.session_state.awaiting_verification = False
        for key in ['pending_name', 'pending_email', 'pending_password']:
            if key in st.session_state:
                del st.session_state[key]

        st.session_state.auth_mode = 'login'

        # Small delay to show success message
        import time
        time.sleep(5)
        st.rerun()
    else:
        st.error("❌ " + message)
        if "expired" in message.lower():
            st.info("💡 You can request a new code using the 'Resend Code' button")

def handle_login(email: str, password: str, remember_me: bool = True):
    """Manejar intento de login con Remember Me"""
    if not email or not password:
        st.error("Please fill in all fields")
        return
    
    success, message, user_info = auth_manager.login_user(email, password, remember_me)
    
    if success:
        st.session_state.authenticated = True
        st.session_state.user_info = user_info
        
        # Save session token for persistence
        if user_info and user_info.get('session_token'):
            save_session_token(user_info['session_token'])

        st.balloons()
        st.rerun()
    else:
        st.error(message)

def handle_registration(full_name: str, email: str, password: str, confirm_password: str):
    """Manejar intento de registro"""
    # Validaciones básicas
    if not all([full_name, email, password, confirm_password]):
        st.error("Please fill in all fields")
        return
    
    if password != confirm_password:
        st.error("Passwords do not match")
        return
    
    # Intentar registrar usuario
    success, message = auth_manager.register_user(email, password, full_name)
    
    if success:
        st.success(message)
        st.info("You can now sign in with your new account!")
        st.session_state.auth_mode = 'login'
        st.rerun()
    else:
        st.error(message)

def show_user_profile():
    """Mostrar perfil del usuario autenticado con opciones de sesión"""
    user_info = st.session_state.user_info
    
    if not user_info:
        logout_user()
        return
    
    # Header de bienvenida
    st.markdown(f"""
    <div class="auth-welcome">
        <h2>Welcome, {user_info['full_name']}! 🎾</h2>
        <p>You're signed in as {user_info['email']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Información de sesión
    session_token = user_info.get('session_token', '')
    if session_token:
        # Show partial token for security
        token_display = session_token[:8] + "..." + session_token[-4:] if len(session_token) > 12 else session_token
        st.markdown(f"""
        <div class="session-info">
            <strong>🔐 Active Session:</strong> {token_display}<br>
            <small>Your session is securely maintained across browser visits</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Perfil en sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="user-profile">
            <div class="profile-header">👤 Your Profile</div>
            <p><strong>Name:</strong> {user_info['full_name']}</p>
            <p><strong>Email:</strong> {user_info['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Botones de perfil
        st.subheader("⚙️ Account Settings")
        
        if st.button("🔧 Edit Profile", use_container_width=True):
            show_profile_editor()
        
        if st.button("🔒 Change Password", use_container_width=True):
            show_password_changer()
        
        st.divider()
        
        # Session management section
        st.subheader("🔐 Session Management")
        
        st.markdown("""
        <div class="logout-buttons">
        """, unsafe_allow_html=True)
        
        # Regular logout button
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            logout_user()
        
        # Sign out from all devices button
        if st.button("🚨 Sign Out All Devices", 
                    use_container_width=True, 
                    help="This will sign you out from all devices and browsers"):
            logout_all_sessions()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Session info in sidebar
        with st.expander("ℹ️ Session Info"):
            st.write("**Current session features:**")
            st.write("• Automatic sign-in on return visits")
            st.write("• Secure token-based authentication")
            st.write("• Session expires automatically")
            st.write("• Multi-device session management")

def show_profile_editor():
    """Mostrar editor de perfil"""
    user_info = st.session_state.user_info
    
    with st.expander("Edit Profile", expanded=True):
        with st.form("edit_profile_form"):
            new_name = st.text_input(
                "Full Name",
                value=user_info['full_name'],
                key="edit_profile_name"
            )
            
            if st.form_submit_button("Update Profile", type="primary"):
                success, message = auth_manager.update_user_profile(
                    user_info['id'], 
                    new_name
                )
                
                if success:
                    st.session_state.user_info['full_name'] = new_name
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

def show_password_changer():
    """Mostrar cambiador de contraseña"""
    user_info = st.session_state.user_info
    
    with st.expander("Change Password", expanded=True):
        st.warning("⚠️ Changing your password will sign you out from all devices for security.")
        
        with st.form("change_password_form"):
            current_password = st.text_input(
                "Current Password",
                type="password",
                key="current_password"
            )
            
            new_password = st.text_input(
                "New Password",
                type="password",
                key="new_password",
                help="Password must be at least 6 characters and contain letters and numbers"
            )
            
            confirm_new_password = st.text_input(
                "Confirm New Password",
                type="password",
                key="confirm_new_password"
            )
            
            if st.form_submit_button("Change Password", type="primary"):
                if new_password != confirm_new_password:
                    st.error("New passwords do not match")
                    return
                
                success, message = auth_manager.change_password(
                    user_info['id'],
                    current_password,
                    new_password
                )
                
                if success:
                    st.success(message)
                    st.info("Please sign in again with your new password.")
                    # The password change method automatically invalidates all sessions
                    logout_user()
                else:
                    st.error(message)