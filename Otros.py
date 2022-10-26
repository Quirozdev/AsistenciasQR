import datetime


def convertir_str_a_hora(hora: str) -> datetime.datetime.time:
    """
    Convierte una hora en formato string a un objeto datetime.datetime.time con formato H:M
    """
    formato = "%H:%M"
    hora_convertida = datetime.datetime.strptime(hora, formato).time()
    return hora_convertida


def convertir_str_a_fecha(fecha: str) -> datetime.datetime.date:
    """
    Convierte una fecha en formato string a un objeto datetime.datetime.date con formato YYYY-MM-DD
    """
    formato = "%Y-%m-%d"
    fecha_convertida = datetime.datetime.strptime(fecha, formato).date()
    return fecha_convertida