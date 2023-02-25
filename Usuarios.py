from flask import Blueprint, render_template, session, request, redirect
from Modelos import db, IntegrantesGrupos, Grupos, Usuarios, DominiosCorreo, CodigosRecuperacion
from passlib.hash import sha256_crypt


usuarios_blueprint = Blueprint('usuarios_blueprint', __name__)




@usuarios_blueprint.route('/modificar_cuenta/<expediente_usuario>', methods=['GET', 'POST'])
def modificar_cuenta(expediente_usuario):
    usuario = Usuarios.query.get(expediente_usuario)
    if request.method == 'GET':
        mensaje = ""
        # se tiene que validar que el usuario que acceda a esta página de modificación sea el mismo usuario que se encuentra logeado
        # esto es para evitar que un usuario logeado pueda modificar la cuenta de otro usuario, mediante la ruta
        if usuario.expediente == session['usuario']:
            return render_template('modificar_cuenta.html', usuario=usuario, mensaje=mensaje)
        else:
            return redirect('/pagina_no_permitida')
    # POST
    else:
        # se obtienen los datos del formulario. El expediente y tipo de usuario no pueden ser modificados,
        # el primero por ser clave primaria y el segundo porque el tipo determina si pertenece o crea grupos
        nombre = request.form['nombre']
        correo = request.form['correo']
        # si se modifico el correo
        if correo != usuario.correo:
            # se tienen que hacer todas las validaciones del correo
            # checamos que ese correo no este siendo usado por otro usuario
            usuario_con_ese_correo = Usuarios.query.filter_by(correo=correo).first()
            # si se encontro a un usuario con ese correo
            if usuario_con_ese_correo is not None:
                mensaje = "Ese correo ya ha sido registrado por otro usuario"
                return render_template('modificar_cuenta.html', usuario=usuario, mensaje=mensaje)
            # se valida el dominio del correo
            dominio_del_correo = correo.split("@")[1]        
            # se necesita checar si el dominio ya ha sido insertado por algun otro docente
            # se checa en la bd si ese registro ya ha sido insertado
            dominio_registrado_en_bd = DominiosCorreo.query.filter_by(dominio_correo=dominio_del_correo).first()
            # si se obtuvo un None, es porque ese dominio no ha sido registrado en la bd por parte de un docente
            if dominio_registrado_en_bd is None:
                # se hace una validacion en la que se checa el tipo de usuario para ver lo que se hace con el dominio
                if usuario.tipo_usuario == "Docente":
                    # se crea ese nuevo dominio para insertarse en la bd
                    nuevo_dominio = DominiosCorreo(dominio_correo=dominio_del_correo)
                    db.session.add(nuevo_dominio)
                # Estudiante
                else:
                    # si es un estudiante el que se esta registrando y el dominio del correo no ha sido registrado por un docente
                    mensaje = f"El dominio del correo que proporcionaste ({dominio_del_correo}) no ha sido registrado por algún docente, se requiere del registro de un docente con ese dominio de correo"
                    return render_template('modificar_cuenta.html', usuario=usuario, mensaje=mensaje)
            # hay que checar si en la tabla codigos_recuperacion hay un registro con ese correo, de ser asi hay que borrarlo
            codigo_registrado = CodigosRecuperacion.query.filter_by(correo=usuario.correo).first()
            if codigo_registrado is not None:
                # si se encontro, se borra
                db.session.delete(codigo_registrado)
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        contrasenia = request.form['contrasenia']
        # se actualiza el registro
        usuario.nombre = nombre
        usuario.correo = correo
        usuario.apellido_paterno = apellido_paterno
        usuario.apellido_materno = apellido_materno
        usuario.contrasenia = sha256_crypt.hash(contrasenia)
        # se guardan los cambios
        db.session.commit()
        # tambien se actualiza la cookie que contiene el tipo y nombre de un usuario para que se muestre en la barra de navegacion 
        session['datos_usuario_logeado'] = f'{usuario.tipo_usuario}: {usuario.nombre} {usuario.apellido_paterno} {usuario.apellido_materno}'
        return redirect(f'/cuenta/{usuario.expediente}')


@usuarios_blueprint.route('/cuenta/<expediente_usuario>')
def cuenta(expediente_usuario):
    usuario = Usuarios.query.get(expediente_usuario)
    # si se encontro a ese usuario en la bd
    if usuario is not None:
        return render_template('cuenta.html', usuario=usuario)
    # en otro caso se renderiza que no se encontro la pagina/cuenta
    else:
        return render_template('404.html')


def validar_pertenencia_usuario(usuario, clave_grupo: str) -> bool:
    """
    Valida que un usuario pertenezca (estudiante) o sea el creador (docente) de un grupo, esto para que
    no pueda acceder a páginas específicas de cada grupo al que no pertenece o no ha creado, esto para evitar
    que el usuario pueda escribir una ruta determinada y pueda acceder sin ser parte del grupo.
    """
    if usuario.tipo_usuario == 'Estudiante':
        # si es estudiante se checa si es integrante de ese grupo
        integrante_grupo = IntegrantesGrupos.query.filter_by(expediente_estudiante=usuario.expediente, clave_grupo=clave_grupo).first()
        # si no se encontró ese registro es porque no es integrante de ese grupo
        if integrante_grupo is None:
            return False
        else:
            return True
    # tipo_usuario = 'Docente'
    else:
        # si es docente se checa si es el propietario de ese grupo
        grupo = Grupos.query.filter_by(expediente_propietario=usuario.expediente, clave=clave_grupo).first()
        # si no se encontró un registro es porque no es propietario de ese grupo
        if grupo is None:
            return False
        else:
            return True

