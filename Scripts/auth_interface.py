"""
Interfaz de Autenticación Mejorada para Sistema de Reservas de Cancha de Tenis
Agrega funcionalidad de Recordarme y gestión de sesión mejorada
"""

import streamlit as st
from auth_manager import auth_manager
from auth_utils import logout_user, logout_all_sessions, init_auth_session_state, require_authentication, \
    save_session_token
from email_config import email_manager
from database_manager import db_manager

# Colores US Open
US_OPEN_BLUE = "#001854"
US_OPEN_LIGHT_BLUE = "#2478CC"
US_OPEN_YELLOW = "#FFD400"


def apply_auth_css():
    """Remover estilos de contenedor de formulario predeterminados de Streamlit"""
    st.markdown("""
    <style>
    /* Remover borde y fondo del contenedor de formulario de Streamlit */
    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        box-shadow: none !important;
    }

    /* Selector alternativo en caso de que el anterior no funcione */
    .stForm {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        box-shadow: none !important;
    }

    /* Remover cualquier borde de formulario */
    form {
        border: none !important;
        background: transparent !important;
    }

    /* Dirigirse al contenedor específico del formulario */
    div[data-testid="stForm"] > div {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

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

    # Verificar si hay token de recuperación en la URL
    try:
        if "reset_token" in st.query_params:
            reset_token = st.query_params["reset_token"]

            # AGREGAR ESTA VALIDACIÓN
            # Validar el token antes de mostrar el formulario
            token_valid, token_message, user_id = auth_manager.validate_password_reset_token(reset_token)

            if token_valid:
                show_reset_password_form(reset_token)
                return False
            else:
                # Token inválido - limpiar URL y mostrar mensaje
                try:
                    del st.query_params["reset_token"]
                except Exception:
                    pass
                st.error("❌ El enlace de recuperación ha expirado o ya fue usado")
                st.info("💡 Solicita un nuevo enlace de recuperación")
                st.session_state.auth_mode = 'forgot_password'
    except Exception:
        pass

    # Verificar si el usuario ya está autenticado
    if st.session_state.get('authenticated', False):
        show_user_profile()
        return True

    # Mostrar formulario según el modo
    if st.session_state.auth_mode == 'forgot_password':
        show_forgot_password_form()
    elif st.session_state.auth_mode == 'login':
        st.markdown('<div class="auth-header">¡Bienvenido de Vuelta!</div>', unsafe_allow_html=True)
        show_login_form()
    else:
        st.markdown('<div class="auth-header">¡Únete a Nosotros!</div>', unsafe_allow_html=True)
        show_registration_form()

    return False


def show_login_form():
    """Mostrar formulario de inicio de sesión con opción Recordarme"""
    st.markdown('<div class="auth-form">', unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown("### Iniciar Sesión")

        email = st.text_input(
            "Dirección de Email",
            placeholder="tu.email@ejemplo.com",
            key="login_email"
        )

        password = st.text_input(
            "Contraseña",
            type="password",
            placeholder="Ingresa tu contraseña",
            key="login_password"
        )

        login_submitted = st.form_submit_button(
            "Iniciar Sesión",
            type="primary",
            use_container_width=True
        )

        if login_submitted:
            handle_login(email, password, True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Enlaces fuera del formulario (usar st.button, NO st.form_submit_button)
    st.markdown("---")

    # Botón de "Olvidaste contraseña"
    if st.button("🔑 ¿Olvidaste tu contraseña?", key="forgot_password_btn", use_container_width=True):
        st.session_state.auth_mode = 'forgot_password'
        st.rerun()

    # Cambiar a registro
    st.markdown(f"""
    <div class="switch-mode">
        <p>¿No tienes una cuenta?</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Crear Nueva Cuenta", key="switch_to_register", use_container_width=True):
        st.session_state.auth_mode = 'register'
        st.rerun()


def show_registration_form():
    """Mostrar formulario de registro con verificación por email"""
    st.markdown('<div class="auth-form">', unsafe_allow_html=True)

    # Verificar si estamos en el paso de verificación de email
    if st.session_state.get('awaiting_verification', False):
        show_email_verification_form()
    else:
        show_initial_registration_form()

    st.markdown('</div>', unsafe_allow_html=True)

    # Cambiar a inicio de sesión
    st.markdown(f"""
    <div class="switch-mode">
        <p>¿Ya tienes una cuenta?</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Iniciar Sesión", key="switch_to_login", use_container_width=True):
        st.session_state.auth_mode = 'login'
        st.session_state.awaiting_verification = False
        # Limpiar datos pendientes al cambiar
        for key in ['pending_name', 'pending_email', 'pending_password']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def show_initial_registration_form():
    """Mostrar formulario inicial de registro"""
    with st.form("registration_form"):
        st.markdown("### Crear Cuenta")

        full_name = st.text_input(
            "Nombre Completo",
            placeholder="Ingresa tu nombre completo",
            key="register_name"
        )

        email = st.text_input(
            "Dirección de Email",
            placeholder="tu.email@ejemplo.com",
            key="register_email"
        )

        password = st.text_input(
            "Contraseña",
            type="password",
            placeholder="Crea una contraseña (mín. 6 caracteres)",
            key="register_password",
            help="La contraseña debe tener al menos 6 caracteres y contener letras y números"
        )

        confirm_password = st.text_input(
            "Confirmar Contraseña",
            type="password",
            placeholder="Confirma tu contraseña",
            key="register_confirm_password"
        )

        register_submitted = st.form_submit_button(
            "Enviar Código de Verificación",
            type="primary",
            use_container_width=True
        )

        if register_submitted:
            handle_initial_registration(full_name, email, password, confirm_password)


def show_email_verification_form():
    """Mostrar formulario de verificación de email"""
    st.success("📧 ¡Código de verificación enviado!")
    st.info(f"Por favor revisa tu email: **{st.session_state.pending_email}**")

    with st.form("verification_form"):
        st.markdown("### Verifica tu Email")

        verification_code = st.text_input(
            "Código de Verificación",
            placeholder="Ingresa el código de 6 caracteres",
            max_chars=6,
            key="verification_code",
            help="Revisa tu email para el código de verificación"
        ).upper()  # Convertir a mayúsculas automáticamente

        col1, col2 = st.columns(2)

        with col1:
            verify_submitted = st.form_submit_button(
                "Verificar y Crear Cuenta",
                type="primary",
                use_container_width=True
            )

        with col2:
            resend_submitted = st.form_submit_button(
                "Reenviar Código",
                use_container_width=True
            )

        if verify_submitted:
            handle_email_verification(verification_code)

        if resend_submitted:
            send_verification_code(st.session_state.pending_email, st.session_state.pending_name)

    # Opción para volver y cambiar email
    if st.button("← Cambiar Dirección de Email", key="change_email"):
        st.session_state.awaiting_verification = False
        st.rerun()


def handle_initial_registration(full_name: str, email: str, password: str, confirm_password: str):
    """Manejar registro inicial y enviar email de verificación"""
    # Validaciones básicas
    if not all([full_name, email, password, confirm_password]):
        st.error("Por favor completa todos los campos")
        return

    if password != confirm_password:
        st.error("Las contraseñas no coinciden")
        return

    # Validar formato de email
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        st.error("Por favor ingresa una dirección de email válida")
        return

    # Verificar si el email ya existe
    try:
        from auth_manager import auth_manager

        with auth_manager.get_connection() as conn:
            cursor = conn.cursor()
            # Asegurar que la tabla users existe primero
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
                st.error("Ya existe una cuenta con este email")
                return

    except Exception as e:
        st.error(f"Error verificando disponibilidad del email: {str(e)}")
        st.warning("No se pudo verificar disponibilidad del email, pero continuando con el registro...")

    # Guardar datos de registro pendientes
    st.session_state.pending_name = full_name.strip()
    st.session_state.pending_email = email.strip().lower()
    st.session_state.pending_password = password

    # Enviar código de verificación
    if send_verification_code(email.strip().lower(), full_name.strip()):
        st.session_state.awaiting_verification = True
        st.rerun()


def send_verification_code(email: str, name: str) -> bool:
    """Enviar código de verificación por email"""
    try:
        # Verificar si el servicio de email está configurado
        if not email_manager.is_configured():
            st.error("El servicio de email no está configurado. Por favor contacta al administrador.")
            return False

        # Generar código
        verification_code = email_manager.generate_verification_code()

        # Guardar en base de datos
        if not db_manager.save_verification_code(email, verification_code):
            st.error("Error guardando código de verificación. Por favor intenta de nuevo.")
            return False

        # Enviar email
        success, message = email_manager.send_verification_email(email, verification_code, name)

        if success:
            st.success("📧 ¡Código de verificación enviado a tu email!")
            st.info("⏰ El código expira en 10 minutos")
            return True
        else:
            st.error(f"Error al enviar email: {message}")
            return False

    except Exception as e:
        st.error(f"Error enviando código de verificación: {str(e)}")
        return False


def handle_email_verification(verification_code: str):
    """Manejar verificación de email"""
    if not verification_code:
        st.error("Por favor ingresa el código de verificación")
        return

    if len(verification_code) != 6:
        st.error("El código de verificación debe tener 6 caracteres")
        return

    # Intentar registro con verificación
    success, message = auth_manager.register_user(
        st.session_state.pending_email,
        st.session_state.pending_password,
        st.session_state.pending_name,
        verification_code
    )

    if success:
        st.success("✅ " + message)
        st.info("¡Ahora puedes iniciar sesión con tu nueva cuenta!")

        # Limpiar datos pendientes
        st.session_state.awaiting_verification = False
        for key in ['pending_name', 'pending_email', 'pending_password']:
            if key in st.session_state:
                del st.session_state[key]

        st.session_state.auth_mode = 'login'

        # Pequeña demora para mostrar mensaje de éxito
        import time
        time.sleep(3)
        st.rerun()
    else:
        st.error("❌ " + message)
        if "expirado" in message.lower():
            st.info("💡 Puedes solicitar un nuevo código usando el botón 'Reenviar Código'")


def handle_login(email: str, password: str, remember_me: bool = True):
    """Manejar intento de inicio de sesión con Recordarme"""
    if not email or not password:
        st.error("Por favor completa todos los campos")
        return

    success, message, user_info = auth_manager.login_user(email, password, remember_me)

    if success:
        st.session_state.authenticated = True
        st.session_state.user_info = user_info

        # Guardar token de sesión para persistencia
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
        st.error("Por favor completa todos los campos")
        return

    if password != confirm_password:
        st.error("Las contraseñas no coinciden")
        return

    # Intentar registrar usuario
    success, message = auth_manager.register_user(email, password, full_name)

    if success:
        st.success(message)
        st.info("¡Ahora puedes iniciar sesión con tu nueva cuenta!")
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

    # Encabezado de bienvenida
    st.markdown(f"""
    <div class="auth-welcome">
        <h2>¡Bienvenido, {user_info['full_name']}! 🎾</h2>
        <p>Has iniciado sesión como {user_info['email']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Información de sesión
    session_token = user_info.get('session_token', '')
    if session_token:
        # Mostrar token parcial por seguridad
        token_display = session_token[:8] + "..." + session_token[-4:] if len(session_token) > 12 else session_token
        st.markdown(f"""
        <div class="session-info">
            <strong>🔐 Sesión Activa:</strong> {token_display}<br>
        </div>
        """, unsafe_allow_html=True)

    # Perfil en sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="user-profile">
            <div class="profile-header">👤 Tu Perfil</div>
            <p><strong>Nombre:</strong> {user_info['full_name']}</p>
            <p><strong>Email:</strong> {user_info['email']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Botones de perfil
        st.subheader("⚙️ Configuración de Cuenta")

        if st.button("🔧 Editar Perfil", use_container_width=True):
            show_profile_editor()

        if st.button("🔒 Cambiar Contraseña", use_container_width=True):
            show_password_changer()

        st.divider()

        # Sección de gestión de sesión
        st.subheader("🔐 Gestión de Sesión")

        st.markdown("""
        <div class="logout-buttons">
        """, unsafe_allow_html=True)

        # Botón de cerrar sesión regular
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            logout_user()

        # Botón de cerrar sesión en todos los dispositivos
        if st.button("🚨 Cerrar Sesión en Todos los Dispositivos",
                     use_container_width=True,
                     help="Esto te desconectará de todos los dispositivos y navegadores"):
            logout_all_sessions()

        st.markdown('</div>', unsafe_allow_html=True)

        # Información de sesión en sidebar
        with st.expander("ℹ️ Info de Sesión"):
            st.write("**Características de sesión actual:**")
            st.write("• Inicio de sesión automático en visitas de regreso")
            st.write("• Autenticación segura basada en tokens")
            st.write("• La sesión expira automáticamente")
            st.write("• Gestión de sesión multi-dispositivo")


def show_profile_editor():
    """Mostrar editor de perfil"""
    user_info = st.session_state.user_info

    with st.expander("Editar Perfil", expanded=True):
        with st.form("edit_profile_form"):
            new_name = st.text_input(
                "Nombre Completo",
                value=user_info['full_name'],
                key="edit_profile_name"
            )

            if st.form_submit_button("Actualizar Perfil", type="primary"):
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

    with st.expander("Cambiar Contraseña", expanded=True):
        st.warning("⚠️ Cambiar tu contraseña te desconectará de todos los dispositivos por seguridad.")

        with st.form("change_password_form"):
            current_password = st.text_input(
                "Contraseña Actual",
                type="password",
                key="current_password"
            )

            new_password = st.text_input(
                "Nueva Contraseña",
                type="password",
                key="new_password",
                help="La contraseña debe tener al menos 6 caracteres y contener letras y números"
            )

            confirm_new_password = st.text_input(
                "Confirmar Nueva Contraseña",
                type="password",
                key="confirm_new_password"
            )

            if st.form_submit_button("Cambiar Contraseña", type="primary"):
                if new_password != confirm_new_password:
                    st.error("Las nuevas contraseñas no coinciden")
                    return

                success, message = auth_manager.change_password(
                    user_info['id'],
                    current_password,
                    new_password
                )

                if success:
                    st.success(message)
                    st.info("Por favor inicia sesión de nuevo con tu nueva contraseña.")
                    # El método de cambio de contraseña invalida automáticamente todas las sesiones
                    logout_user()
                else:
                    st.error(message)


def show_forgot_password_form():
    """Mostrar formulario de recuperación de contraseña"""
    st.markdown('<div class="auth-header">Recuperar Contraseña</div>', unsafe_allow_html=True)

    with st.form("forgot_password_form"):
        st.markdown("### Recuperar tu Contraseña")
        st.info("Te enviaremos un enlace de recuperación a tu email registrado.")

        email = st.text_input(
            "Dirección de Email",
            placeholder="tu.email@ejemplo.com",
            key="forgot_password_email"
        )

        submitted = st.form_submit_button(
            "Enviar Enlace de Recuperación",
            type="primary",
            use_container_width=True
        )

        if submitted:
            handle_forgot_password(email)

    # Botón para volver al login
    if st.button("← Volver al Inicio de Sesión", key="back_to_login"):
        st.session_state.auth_mode = 'login'
        st.rerun()


def show_reset_password_form(reset_token: str):
    """Mostrar formulario de nueva contraseña"""
    st.markdown('<div class="auth-header">Crear Nueva Contraseña</div>', unsafe_allow_html=True)

    # Validar token primero
    token_valid, token_message, user_id = auth_manager.validate_password_reset_token(reset_token)

    if not token_valid:
        st.error(f"❌ {token_message}")
        st.info("El enlace puede haber expirado. Solicita una nueva recuperación de contraseña.")

        if st.button("Solicitar Nuevo Enlace"):
            st.session_state.auth_mode = 'forgot_password'
            st.rerun()
        return

    st.success(f"✅ {token_message}")

    with st.form("reset_password_form"):
        st.markdown("### Nueva Contraseña")

        new_password = st.text_input(
            "Nueva Contraseña",
            type="password",
            placeholder="Ingresa tu nueva contraseña",
            key="new_password",
            help="La contraseña debe tener al menos 6 caracteres y contener letras y números"
        )

        confirm_password = st.text_input(
            "Confirmar Nueva Contraseña",
            type="password",
            placeholder="Confirma tu nueva contraseña",
            key="confirm_new_password"
        )

        submitted = st.form_submit_button(
            "Actualizar Contraseña",
            type="primary",
            use_container_width=True
        )

        if submitted:
            handle_reset_password(reset_token, new_password, confirm_password)


def handle_forgot_password(email: str):
    """Manejar solicitud de recuperación de contraseña"""
    if not email:
        st.error("Por favor ingresa tu dirección de email")
        return

    # Validar formato de email
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        st.error("Por favor ingresa una dirección de email válida")
        return

    # Crear token de recuperación
    success, message, reset_token = auth_manager.create_password_reset_token(email)

    if success and reset_token:
        # Obtener información del usuario para el email
        with auth_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT full_name FROM users WHERE email = ?', (email.strip().lower(),))
            user_data = cursor.fetchone()
            user_name = user_data[0] if user_data else "Usuario"

        # Enviar email
        if email_manager.is_configured():
            email_success, email_message = email_manager.send_password_reset_email(
                email, reset_token, user_name
            )

            if email_success:
                st.success("📧 ¡Enlace de recuperación enviado!")
                st.info("Revisa tu email y sigue las instrucciones para restablecer tu contraseña.")
                st.warning("⏰ El enlace expira en 30 minutos.")
            else:
                st.error(f"Error enviando email: {email_message}")
        else:
            st.error("Servicio de email no configurado. Contacta al administrador.")
    else:
        # Por seguridad, no revelar si el email existe o no
        st.success("📧 Si existe una cuenta con ese email, recibirás un enlace de recuperación.")
        st.info("Revisa tu email y sigue las instrucciones.")


def handle_reset_password(reset_token: str, new_password: str, confirm_password: str):
    """Manejar actualización de contraseña"""
    if not new_password or not confirm_password:
        st.error("Por favor completa todos los campos")
        return

    if new_password != confirm_password:
        st.error("Las contraseñas no coinciden")
        return

    # Resetear contraseña
    success, message = auth_manager.reset_password_with_token(reset_token, new_password)

    if success:
        st.success("✅ " + message)
        st.info("🔐 Por seguridad, todas tus sesiones han sido cerradas.")
        st.balloons()

        # AGREGAR ESTA PARTE - Limpiar token de la URL
        try:
            if "reset_token" in st.query_params:
                del st.query_params["reset_token"]
        except Exception:
            pass

        # Redirigir al login después de un momento
        import time
        time.sleep(3)
        st.session_state.auth_mode = 'login'
        st.rerun()
    else:
        st.error("❌ " + message)