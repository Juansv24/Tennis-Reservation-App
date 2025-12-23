import pytz
from datetime import datetime, date

# Zona horaria de Colombia
COLOMBIA_TZ = pytz.timezone('America/Bogota')

# Nombres de días de la semana en español
SPANISH_DAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

def get_colombia_now():
    """Obtener fecha y hora actual en zona horaria de Colombia"""
    return datetime.now(COLOMBIA_TZ)

def get_colombia_today():
    """Obtener fecha actual en zona horaria de Colombia"""
    return get_colombia_now().date()

def format_date_display(date_str: str) -> str:
    """
    Formatear fecha en formato legible con día de la semana

    Args:
        date_str: Fecha en formato 'YYYY-MM-DD'

    Returns:
        String en formato 'Día DD/MM/YYYY' (ej: 'Lun 15/01/2025')
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d/%m/%Y')
        day_name = SPANISH_DAYS[date_obj.weekday()]
        return f"{day_name} {formatted_date}"
    except Exception:
        return date_str

def format_datetime_display(datetime_str: str) -> str:
    """
    Formatear datetime en formato legible

    Args:
        datetime_str: DateTime en formato ISO

    Returns:
        String en formato 'DD/MM/YYYY HH:MM' (ej: '15/01/2025 14:30')
    """
    try:
        dt_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt_obj.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return datetime_str

def format_date_short(date_str: str) -> str:
    """
    Formatear fecha en formato corto DD/MM/YYYY

    Args:
        date_str: Fecha en formato 'YYYY-MM-DD'

    Returns:
        String en formato 'DD/MM/YYYY' (ej: '15/01/2025')
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except Exception:
        return date_str

def get_day_name(date_str: str) -> str:
    """
    Obtener nombre del día de la semana en español

    Args:
        date_str: Fecha en formato 'YYYY-MM-DD'

    Returns:
        Nombre del día (ej: 'Lun', 'Mar', etc.)
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return SPANISH_DAYS[date_obj.weekday()]
    except Exception:
        return ''