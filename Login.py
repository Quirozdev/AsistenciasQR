from flask import Blueprint, redirect, render_template, request, session
from passlib.hash import sha256_crypt
from Modelos import Usuarios


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
    que define si el usuario está logeado (session['usuario]) es eliminado
    """
    session.clear()
    return redirect("/")