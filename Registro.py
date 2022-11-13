from flask import Blueprint, redirect, render_template, request, session
from passlib.hash import sha256_crypt
from Modelos import db, Usuarios, DominiosCorreo


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
        # se obtiene el dominio del correo ingresado, los correos van a tener la forma:
        # algo@dominio.com
        # de modo que al separar el string por la arroba, se obtiene una lista con 2 elementos:
        # correo.split("@") -> lista = ['algo', 'dominio.com']
        # el dominio es el elemento con indice 1, por lo que para obtenerlo:
        # dominio_del_correo = lista[1]
        dominio_del_correo = correo.split("@")[1]        
        # se necesita checar si el dominio ya ha sido insertado por algun otro docente
        # se checa en la bd si ese registro ya ha sido insertado
        dominio_registrado_en_bd = DominiosCorreo.query.filter_by(dominio_correo=dominio_del_correo).first()
        # si se obtuvo un None, es porque ese dominio no ha sido registrado en la bd por parte de un docente
        if dominio_registrado_en_bd is None:
            # se hace una validacion en la que se checa el tipo de usuario para ver lo que se hace con el dominio
            if tipo_usuario == "Docente":
                # se crea ese nuevo dominio para insertarse en la bd
                nuevo_dominio = DominiosCorreo(dominio_correo=dominio_del_correo)
                db.session.add(nuevo_dominio)
            # Estudiante
            else:
                # si es un estudiante el que se esta registrando y el dominio del correo no ha sido registrado por un docente
                mensaje = f"El dominio del correo que proporcionaste ({dominio_del_correo}) no ha sido registrado por algún docente, se requiere del registro de un docente con ese dominio de correo"
                return render_template('registro.html', mensaje=mensaje)
        # se encripta la contrasenia
        contrasenia = sha256_crypt.hash(request.form['contrasenia'])
        # con los datos obtenidos del formulario, se agrega a ese usuario en la base de datos
        nuevo_usuario = Usuarios(expediente=expediente, nombre=nombre, apellido_paterno=apellido_paterno, apellido_materno=apellido_materno, correo=correo, tipo_usuario=tipo_usuario, contrasenia=contrasenia)
        db.session.add(nuevo_usuario)
        # se insertan los cambios
        db.session.commit()
        # redireccionamos a index y asignamos la sesion de que el usuario ya se ha logeado.
        session['usuario'] = expediente
        # tambien se guarda el tipo y nombre de un usuario para que se muestre en la barra de navegacion 
        session['datos_usuario_logeado'] = f'{tipo_usuario}: {nombre} {apellido_paterno} {apellido_materno}'
        return redirect('/')
