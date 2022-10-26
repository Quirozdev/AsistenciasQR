from flask import Blueprint, redirect, render_template, request, session
from passlib.hash import sha256_crypt
from Modelos import db, Usuarios


registro_blueprint = Blueprint('registro_blueprint', __name__)


@registro_blueprint.route('/registro', methods=['GET', 'POST'])
@registro_blueprint.route('/registro/', methods=['GET', 'POST'])
def registro():
    mensaje = ""
    if request.method == 'GET':
        return render_template("registro.html", mensaje=mensaje)
    # POST
    else:
        expediente = request.form['expediente']
        # se valida que el expediente no contenga espacios en blanco (esto es para evitar un problema cuando se modifica la asistencia de un estudiante y se quieren obtener sus datos de asistencia)
        if " " in expediente:
            mensaje = "No puedes usar espacios en blanco para el campo de expediente"
            return render_template('registro.html', mensaje=mensaje)
        correo = request.form['correo']
        usuario = Usuarios.query.get(expediente)
        # validar que estos datos sean unicos y no se repitan
        # si se encontro a un usuario con ese expediente en la bd
        if usuario is not None:
            mensaje = "Ese expediente ya ha sido registrado por otro usuario"
            return render_template('registro.html', mensaje=mensaje)
        # se obtiene una lista de los objetos usuario con el correo dado
        usuarios_con_ese_correo = Usuarios.query.filter_by(correo=correo).all()
        # si esa lista no esta vacia, es porque ya hay un usuario con ese correo
        if len(usuarios_con_ese_correo) > 0:
            mensaje = "Ese correo ya ha sido registrado por otro usuario"
            return render_template('registro.html', mensaje=mensaje)
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        tipo_usuario = request.form['tipo_usuario']
        # se encripta la contrasenia
        contrasenia = sha256_crypt.hash(request.form['contrasenia'])
        # con los datos obtenidos del formulario, se agrega a ese usuario en la base de datos
        nuevo_usuario = Usuarios(expediente=expediente, nombre=nombre, apellido_paterno=apellido_paterno, apellido_materno=apellido_materno, correo=correo, tipo_usuario=tipo_usuario, contrasenia=contrasenia)
        db.session.add(nuevo_usuario)
        # se insertan los cambios
        db.session.commit()
        # redireccionamos a index y asignamos la sesion de que el usuario ya se ha logeado.
        session['usuario'] = expediente
        return redirect('/')
