from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

db = SQLAlchemy()

class Usuarios(db.Model):
    expediente = db.Column(db.String(55), primary_key=True)
    nombre = db.Column(db.String(55), nullable=False)
    apellido_paterno = db.Column(db.String(55), nullable=False)
    apellido_materno = db.Column(db.String(55), nullable=False)
    correo = db.Column(db.String(255), unique=True, nullable=False)
    tipo_usuario = db.Column(db.String(15), nullable=False)
    contrasenia = db.Column(db.String(110), nullable=False)

    def __str__(self):
        return f'{self.expediente}, {self.nombre}, {self.apellido_paterno}, {self.apellido_materno}'


class Grupos(db.Model):
    clave = db.Column(db.String(255), primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(510), nullable=False)
    expediente_propietario = db.Column(db.String(55), ForeignKey('usuarios.expediente'), nullable=False)


class IntegrantesGrupos(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement="auto")
    clave_grupo = db.Column(db.String(255), ForeignKey('grupos.clave'), nullable=False)
    expediente_estudiante = db.Column(db.String(55), ForeignKey('usuarios.expediente'), nullable=False)


class CodigosQr(db.Model):
    clave = db.Column(db.String(255), primary_key=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_asistencia = db.Column(db.Time, nullable=False)
    hora_retardo = db.Column(db.Time, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    clave_grupo = db.Column(db.String(255), ForeignKey('grupos.clave'), nullable=False)


class Asistencias(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement="auto")
    fecha = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(15), nullable=False)
    expediente_estudiante = db.Column(db.String(55), ForeignKey('usuarios.expediente'), nullable=False)
    clave_grupo = db.Column(db.String(255), ForeignKey('grupos.clave'), nullable=False)


class DominiosCorreo(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement="auto")
    dominio_correo = db.Column(db.String(255), nullable=False)


class CodigosRecuperacion(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement="auto")
    correo = db.Column(db.String(255), unique=True, nullable=False)
    codigo_recuperacion = db.Column(db.String(255), nullable=False)