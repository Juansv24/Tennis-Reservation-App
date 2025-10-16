import pytz
from datetime import datetime, date

# Zona horaria de Colombia
COLOMBIA_TZ = pytz.timezone('America/Bogota')

# Nombres de días y meses en español (constantes compartidas)
DAYS_SHORT_ES = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']
DAYS_FULL_ES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
MONTHS_SHORT_ES = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
MONTHS_FULL_ES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

def get_colombia_now():
    """Obtener fecha y hora actual en zona horaria de Colombia"""
    return datetime.now(COLOMBIA_TZ)

def get_colombia_today():
    """Obtener fecha actual en zona horaria de Colombia"""
    return get_colombia_now().date()

def format_date_short(date_obj: date) -> str:
    """
    Formatear fecha en formato corto
    Ejemplo: "LUN 15 ENE"
    """
    day_name = DAYS_SHORT_ES[date_obj.weekday()]
    month_name = MONTHS_SHORT_ES[date_obj.month - 1]
    return f"{day_name} {date_obj.day} {month_name}"

def format_date_full(date_obj: date) -> str:
    """
    Formatear fecha en formato completo
    Ejemplo: "Lunes, 15 de Enero de 2025"
    """
    day_name = DAYS_FULL_ES[date_obj.weekday()]
    month_name = MONTHS_FULL_ES[date_obj.month - 1]
    return f"{day_name}, {date_obj.day} de {month_name} de {date_obj.year}"