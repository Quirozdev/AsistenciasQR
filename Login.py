from flask import Blueprint, redirect, render_template, request, session
from passlib.hash import sha256_crypt
from Modelos import Usuarios, CodigosRecuperacion, db
from Otros import mandar_correo
import random


login_blueprint = Blueprint('login_blueprint', __name__)


@login_blueprint.route('/login', methods=['GET', 'POST'])
@login_blueprint.route('/login/', methods=['GET', 'POST'])
def login():
    mensaje = ""
    if request.method == 'GET':
        return render_template('login.html', mensaje=mensaje)
    # POST
    else:
        expediente = request.form['expediente']
        # se obtiene al usuario con el expediente ingresado desde la base de datos
        usuario = Usuarios.query.get(expediente)
        # si se encontro a un usuario con ese expediente
        if usuario is not None:
            contrasenia = request.form['contrasenia']
            # contrasenia guardada en la base de datos
            contrasenia_guardada = usuario.contrasenia
            # se comparan ambas contrasenias
            coinciden = sha256_crypt.verify(
                        contrasenia, contrasenia_guardada)
            if (coinciden == True):
                # se queda guardada la "cookie" de inicio de sesion
                session['usuario'] = expediente
                # tambien su tipo y nombre
                session['datos_usuario_logeado'] = f'{usuario.tipo_usuario}: {usuario.nombre} {usuario.apellido_paterno} {usuario.apellido_materno}'
                # se redirecciona al index
                return redirect('/')
            else:
                mensaje = "Contraseña incorrecta"
                return render_template('login.html', mensaje=mensaje)
        else:
            mensaje = "No hay un usuario registrado con ese expediente"
            return render_template('login.html', mensaje=mensaje)


@login_blueprint.route('/logout')
@login_blueprint.route('/logout/')
def logout():
    """
    Esta función sirve para cerrar sesión, borra la llave de 'usuario' del 'diccionario' session, de modo que uno de los valores
    que define si el usuario está logeado (session['usuario']) es eliminado, borra todas las cookies del sitio.
    """
    session.clear()
    return redirect("/")


@login_blueprint.route('/recuperar_contrasenia', methods=['GET', 'POST'])
@login_blueprint.route('/recuperar_contrasenia/', methods=['GET', 'POST'])
def recuperar_contrasenia():
    if request.method == 'GET':
        mensaje = ""
        return render_template('recuperar_contrasenia.html', mensaje=mensaje)
    # POST
    else:
        correo = request.form['correo']
        # se obtiene la informacion del usuario con ese correo, como los correos son unicos y no se pueden repetir se obtiene al primero
        usuario = Usuarios.query.filter_by(correo=correo).first()
        # si no se encuentra a un usuario registrado con ese correo
        if usuario is None:
            mensaje = "No hay ningún usuario registrado con el correo que proporcionaste"
            return render_template('recuperar_contrasenia.html', mensaje=mensaje)
        # se va a generar un codigo de 6 cifras que es común verlo en algunas páginas que tienen un proceso de recuperación de contraseñas similares
        codigo_recuperacion = random.randint(100000, 999999)
        # se tiene que checar si a ese correo no se le ha mandado ya un codigo de recuperacion
        codigo_recuperacion_bd = CodigosRecuperacion.query.filter_by(correo=correo).first()
        if codigo_recuperacion_bd is None:
            # se crea un nuevo registro y se guarda ese registro en la tabla de codigos de recuperacion
            nuevo_codigo_recuperacion = CodigosRecuperacion(correo=correo, codigo_recuperacion=str(codigo_recuperacion))
            db.session.add(nuevo_codigo_recuperacion)
            # se insertan los cambios
            db.session.commit()
        else:
            # se actualiza el registro (el codigo de recuperacion)
            codigo_recuperacion_bd.codigo_recuperacion = str(codigo_recuperacion)
            db.session.commit()
        # se manda el correo de recuperacion
        mandar_correo_recuperacion(correo, codigo_recuperacion, usuario)
        mensaje = "Se ha envíado el código de recuperación a tu correo, sigue las instrucciones en el mensaje"
        return render_template('recuperar_contrasenia.html', mensaje=mensaje)


@login_blueprint.route('/cambiar_contrasenia', methods=['GET', 'POST'])
@login_blueprint.route('/cambiar_contrasenia/', methods=['GET', 'POST'])
def introducir_codigo_recuperacion():
    if request.method == "GET":
        mensaje = ""
        return render_template('cambiar_contrasenia.html', mensaje=mensaje)
    # POST
    else:
        # se obtienen los datos del formulario
        correo = request.form['correo']
        # se checa si el correo proporcionado pertenece a algun usuario
        usuario = Usuarios.query.filter_by(correo=correo).first()
        if usuario is None:
            mensaje = "No hay ningún usuario registrado con el correo que proporcionaste"
            return render_template('cambiar_contrasenia.html', mensaje=mensaje)
        codigo_recuperacion = request.form['codigo_recuperacion']
        codigo_recuperacion_bd = CodigosRecuperacion.query.filter_by(correo=correo).first()
        # si no se encuentra ningun registro del codigo de recuperacion para el correo dado
        if codigo_recuperacion_bd is None:
            mensaje = "No se ha generado un código de recuperación para el correo que proporcionaste"
            return render_template('cambiar_contrasenia.html', mensaje=mensaje)
        # se valida si el codigo de recuperacion en el formulario es el mismo que esta registrado en la base de datos, ambos son string por lo que no se necesita realizar una conversion
        # si no coinciden
        if codigo_recuperacion != codigo_recuperacion_bd.codigo_recuperacion:
            mensaje = "Código de recuperación incorrecto"
            return render_template('cambiar_contrasenia.html', mensaje=mensaje)
        contrasenia = request.form['contrasenia']
        contrasenia_confirmada = request.form['confirmar_contrasenia']
        # se valida que ambas contrasenias sean iguales
        if contrasenia != contrasenia_confirmada:
            mensaje = "Las contraseñas deben de coincidir"
            return render_template('cambiar_contrasenia.html', mensaje=mensaje)
        # si todo salio bien, entonces se ejecuta lo siguiente
        # se encripta la contrasenia
        contrasenia_encriptada = sha256_crypt.hash(contrasenia)
        # se actualiza la contrasenia del registro de ese usuario
        usuario.contrasenia = contrasenia_encriptada
        # se borra ese registro de codigo de recuperacion en la base de datos
        db.session.delete(codigo_recuperacion_bd)
        # se guardan los cambios
        db.session.commit()
        return redirect('/login')


def mandar_correo_recuperacion(correo_destinatario: str, codigo_recuperacion, usuario):
    """
    Manda un correo de recuperación a un correo destinatario de un usuario registrado, envíandole un código de recuperación.
    """
    asunto = "Recuperación de contraseña"
    nombre_usuario = f'{usuario.nombre} {usuario.apellido_paterno} {usuario.apellido_materno}'
    host = 'https://asistenciasqr.pythonanywhere.com'
    # Aquí se pone el contenido del mensaje, que también puede ser un html
    contenido_mensaje = f'<!DOCTYPE html><html><head></head><body><h4>Hola, {nombre_usuario}</h4><p>Para recuperar tu contraseña, introduce el siguiente código de recuperación:</p></br><h3>{codigo_recuperacion}</h3><p>En el siguiente enlace:</p></br><a href="{host}/cambiar_contrasenia">Cambiar mi contraseña</a></br><p>Si tu no iniciaste este proceso, ignora este correo y no pasará nada</p></br><p>Saludos,</p></br><p>-El equipo de AsistenciasQR</p></body></html>'
    mandar_correo(asunto, correo_destinatario, contenido_mensaje)