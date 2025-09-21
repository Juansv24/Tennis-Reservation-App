"""
Utilidades de Autenticación para Streamlit Cloud
Usa parámetros de consulta URL como método principal de persistencia
"""

import streamlit as st
from auth_manager import auth_manager
import time


def save_session_token(token: str):
    """Guardar token de sesión usando parámetros de consulta URL"""
    # Almacenar en estado de sesión para sesión actual
    st.session_state.session_token = token
    st.session_state.token_saved_at = time.time()

    # Guardar en URL para persistencia entre actualizaciones
    try:
        st.query_params["session_token"] = token
    except Exception as e:
        st.warning(f"No se pudo guardar la sesión: {e}")


def get_saved_session_token():
    """Obtener token de sesión guardado del estado de sesión o URL"""

    # Primero intentar estado de sesión (sesión actual)
    if (hasattr(st.session_state, 'session_token') and
            st.session_state.session_token):
        return st.session_state.session_token

    # Luego intentar parámetros de consulta URL (para actualizaciones/nuevas pestañas)
    try:
        if "session_token" in st.query_params:
            token = st.query_params["session_token"]
            if token:
                # Restaurar al estado de sesión
                st.session_state.session_token = token
                st.session_state.token_saved_at = time.time()
                return token
    except Exception:
        pass

    return None


def clear_session_token():
    """Limpiar token de sesión de todas las fuentes"""
    # Limpiar estado de sesión
    if hasattr(st.session_state, 'session_token'):
        st.session_state.session_token = None
    if hasattr(st.session_state, 'token_saved_at'):
        st.session_state.token_saved_at = None

    # Limpiar parámetros URL
    try:
        if "session_token" in st.query_params:
            del st.query_params["session_token"]
    except Exception:
        pass


def try_auto_login():
    """
    Intentar inicio de sesión automático usando token de sesión guardado

    Esta función se ejecuta automáticamente al cargar la aplicación para
    restaurar la sesión del usuario si tiene un token válido guardado.

    Returns:
        bool: True si el inicio de sesión automático fue exitoso, False si no
    """

    # PASO 1: Verificar si el usuario ya está autenticado
    # Si ya está autenticado, no necesitamos hacer nada más
    if st.session_state.get('authenticated', False):
        return True

    # PASO 2: Intentar obtener token de sesión guardado
    # Primero del estado de sesión, luego de los parámetros URL
    session_token = get_saved_session_token()

    # Si no hay token guardado, no se puede hacer login automático
    if not session_token:
        return False

    try:
        # PASO 3: Validar sesión con el servidor
        # Esta llamada también configura el contexto RLS automáticamente
        user_info = auth_manager.validate_session(session_token)

        if user_info:
            # PASO 4: Sesión válida - restaurar autenticación en la aplicación
            st.session_state.authenticated = True
            st.session_state.user_info = user_info

            # PASO 5: Asegurar que el token esté guardado correctamente
            # Esto actualiza tanto el estado de sesión como los parámetros URL
            save_session_token(session_token)

            # PASO 6: Marcar para mostrar notificación de login automático
            # Esto le dice al usuario que su sesión fue restaurada
            st.session_state.show_auto_login_notice = True

            # Login automático exitoso
            return True

        else:
            # PASO 7: Sesión inválida - limpiar todos los tokens guardados
            # Esto incluye estado de sesión y parámetros URL
            clear_session_token()

            # Login automático falló
            return False

    except Exception as e:
        # PASO 8: Error durante validación - limpiar todo por seguridad
        clear_session_token()

        # Opcional: Log del error para debugging (comentar en producción)
        print(f"Error en try_auto_login: {str(e)}")

        return False

def require_authentication():
    """Verificar autenticación con inicio de sesión automático"""
    # Siempre intentar inicio de sesión automático primero
    return try_auto_login()


def get_current_user():
    """Obtener información del usuario actual"""
    if require_authentication():
        return st.session_state.user_info
    return None


def logout_user():
    """Cerrar sesión del usuario y limpiar todos los datos de sesión"""

    # Obtener token de sesión antes de limpiar
    session_token = None
    if hasattr(st.session_state, 'user_info') and st.session_state.user_info:
        session_token = st.session_state.user_info.get('session_token')

    # Destruir sesión del servidor
    if session_token:
        try:
            auth_manager.destroy_session(session_token)
        except Exception:
            pass  # Continuar incluso si falla la limpieza del servidor

    # Limpiar estado de autenticación
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.auth_mode = 'login'

    # Limpiar tokens de sesión
    clear_session_token()

    # Limpiar estados de reservas
    reservation_keys = ['selected_hours', 'selected_date', 'show_auto_login_notice']
    for key in reservation_keys:
        if key in st.session_state:
            del st.session_state[key]

    st.success("✅ Has cerrado sesión exitosamente")
    st.rerun()


def logout_all_sessions():
    """Cerrar sesión desde todos los dispositivos"""
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

    # Estados de verificación de email
    if 'awaiting_verification' not in st.session_state:
        st.session_state.awaiting_verification = False
    if 'pending_name' not in st.session_state:
        st.session_state.pending_name = None
    if 'pending_email' not in st.session_state:
        st.session_state.pending_email = None
    if 'pending_password' not in st.session_state:
        st.session_state.pending_password = None
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'

    # Intentar inicio de sesión automático en inicialización
    try_auto_login()