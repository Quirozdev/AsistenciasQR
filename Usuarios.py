from flask import Blueprint, render_template, session, request, redirect
from Modelos import db, IntegrantesGrupos, Grupos, Usuarios
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
        # se obtienen los datos del formulario. El expediente, tipo de usuario y correo no pueden ser modificados,
        # el primero por ser clave primaria, el segundo porque el tipo determina si pertenece o crea grupos
        # y el tercero porque por que el usuario podria cambiar el dominio de su correo al de una institucion
        # que no este registrada mediante un docente
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        contrasenia = request.form['contrasenia']
        # se actualiza el registro
        usuario.nombre = nombre
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

