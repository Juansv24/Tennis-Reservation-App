"""
Simplified Authentication Interface for Tennis Court Reservation System
Removed Remember Me functionality and persistent session management
"""

import streamlit as st
from auth_manager import auth_manager
from auth_utils import logout_user, init_auth_session_state, require_authentication

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
    """Show authentication interface"""
    apply_auth_css()

    # Check if user is already authenticated
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
    """Show login form without Remember Me option"""
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
            handle_login(email, password)

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
    """Show registration form"""
    st.markdown('<div class="auth-form">', unsafe_allow_html=True)

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
            "Create Account",
            type="primary",
            use_container_width=True
        )

        if register_submitted:
            handle_registration(full_name, email, password, confirm_password)

    st.markdown('</div>', unsafe_allow_html=True)

    # Switch to login
    st.markdown(f"""
    <div class="switch-mode">
        <p>Already have an account?</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign In Instead", key="switch_to_login", use_container_width=True):
        st.session_state.auth_mode = 'login'
        st.rerun()

def handle_login(email: str, password: str):
    """Handle login attempt without Remember Me"""
    if not email or not password:
        st.error("Please fill in all fields")
        return

    success, message, user_info = auth_manager.login_user(email, password, remember_me=False)

    if success:
        st.session_state.authenticated = True
        st.session_state.user_info = user_info

        st.success(f"Welcome back, {user_info['full_name']}!")
        st.balloons()
        st.rerun()
    else:
        st.error(message)

def handle_registration(full_name: str, email: str, password: str, confirm_password: str):
    """Handle registration attempt"""
    # Basic validations
    if not all([full_name, email, password, confirm_password]):
        st.error("Please fill in all fields")
        return

    if password != confirm_password:
        st.error("Passwords do not match")
        return

    # Try to register user
    success, message = auth_manager.register_user(email, password, full_name)

    if success:
        st.success(message)
        st.info("You can now sign in with your new account!")
        st.session_state.auth_mode = 'login'
        st.rerun()
    else:
        st.error(message)

def show_user_profile():
    """Show authenticated user profile without session management options"""
    user_info = st.session_state.user_info

    if not user_info:
        logout_user()
        return

    # Welcome header
    st.markdown(f"""
    <div class="auth-welcome">
        <h2>Welcome, {user_info['full_name']}! 🎾</h2>
        <p>You're signed in as {user_info['email']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Profile in sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="user-profile">
            <div class="profile-header">👤 Your Profile</div>
            <p><strong>Name:</strong> {user_info['full_name']}</p>
            <p><strong>Email:</strong> {user_info['email']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Profile buttons
        st.subheader("⚙️ Account Settings")

        if st.button("🔧 Edit Profile", use_container_width=True):
            show_profile_editor()

        if st.button("🔒 Change Password", use_container_width=True):
            show_password_changer()

        st.divider()

        # Simple logout section
        st.subheader("🚪 Sign Out")

        if st.button("Sign Out", use_container_width=True, type="secondary"):
            logout_user()

        # Session info
        with st.expander("ℹ️ Session Info"):
            st.write("**Current session features:**")
            st.write("• Session lasts until browser is closed")
            st.write("• Simple email/password authentication")
            st.write("• No persistent login across visits")

def show_profile_editor():
    """Show profile editor"""
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
    """Show password changer"""
    user_info = st.session_state.user_info

    with st.expander("Change Password", expanded=True):
        st.warning("⚠️ Changing your password will sign you out for security.")

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
                    logout_user()
                else:
                    st.error(message)