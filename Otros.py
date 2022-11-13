import datetime
import smtplib
from email.message import EmailMessage
from pytz import timezone


def obtener_fecha_actual() -> datetime.datetime:
    """
    Regresa la fecha actual con la zona horaria de Hermosillo.
    """
    fecha_actual = datetime.datetime.now(timezone('UTC'))
    fecha_zona_horaria_correspondiete = fecha_actual.astimezone(timezone('America/Hermosillo'))
    return fecha_zona_horaria_correspondiete



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


def mandar_correo(asunto: str, correo_destinatario: str, contenido_mensaje: str):
    """
    Recibe como parámetros el asunto de un mensaje, el correo destinatario y el contenido del mensaje, 
    envía un correo con el servidor de correo de Gmail con esos parámetros.
    """
    mensaje = EmailMessage()
    correo_remitente = "eqingsoftware12@gmail.com"
    # esta es una contrasenia de aplicacion que gmail nos proporciona para aplicaciones "no tan seguras"
    contrasenia_correo_remitente = "pqymukemamuhzida"
    mensaje['Subject'] = asunto
    mensaje['From'] = correo_remitente
    mensaje['To'] = correo_destinatario
    mensaje.set_content(contenido_mensaje, subtype='html')
    # el servidor de correo electronico desde donde se va a enviar el mensaje va a ser Gmail
    correo_smtp = "smtp.gmail.com"
    # el puerto común utilizado para este servicio es el 587
    servidor = smtplib.SMTP(correo_smtp, '587')
    # se hace una conexión con el servidor y haciendolo de manera segura con el modo TLS
    # servidor.ehlo()
    servidor.starttls()
    # se hace un login al servidor
    servidor.login(correo_remitente, contrasenia_correo_remitente)
    # se envia el correo
    servidor.send_message(mensaje)
    # se cierra la conexión con el servidor
    servidor.quit()