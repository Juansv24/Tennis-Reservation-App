import pytz
from datetime import datetime, date

# Zona horaria de Colombia
COLOMBIA_TZ = pytz.timezone('America/Bogota')

def get_colombia_now():
    """Obtener fecha y hora actual en zona horaria de Colombia"""
    return datetime.now(COLOMBIA_TZ)

def get_colombia_today():
    """Obtener fecha actual en zona horaria de Colombia"""
    return get_colombia_now().date()