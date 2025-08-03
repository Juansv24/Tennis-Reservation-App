import pytz
from datetime import datetime, date

COLOMBIA_TZ = pytz.timezone('America/Bogota')

def get_colombia_now():
    """Get current datetime in Colombia timezone"""
    return datetime.now(COLOMBIA_TZ)

def get_colombia_today():
    """Get current date in Colombia timezone"""
    return get_colombia_now().date()