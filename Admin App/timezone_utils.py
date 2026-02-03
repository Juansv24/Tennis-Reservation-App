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

