from flask import Flask, render_template, request, session, redirect
from Modelos import db, Usuarios
from Registro import registro_blueprint
from Login import login_blueprint
from Grupos import grupos_blueprint, crear_grupo_asistencias, obtener_grupos, unirse_grupo_asistencias
from CodigosQR import codigos_qr_blueprint
from Asistencias import asistencias_blueprint
from Usuarios import usuarios_blueprint




app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = "mysql://{username}:{password}@{hostname}/{databasename}".format(
    username="AsistenciasQR",
    password="basedatos3012",
    hostname="AsistenciasQR.mysql.pythonanywhere-services.com",
    databasename="AsistenciasQR$asistencias_qr_db",
)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Para utilizar las cookies del session
app.secret_key = "jBzTos1bzR92pTQ7"

with app.app_context():
    db.create_all()

# esto permite que se pueda rutear a otras partes de la página en distintos archivos .py, para que no
# se encuentre toda la parte del ruteo en un solo archivo
app.register_blueprint(registro_blueprint)
app.register_blueprint(login_blueprint)
app.register_blueprint(grupos_blueprint)
app.register_blueprint(codigos_qr_blueprint)
app.register_blueprint(asistencias_blueprint)
app.register_blueprint(usuarios_blueprint)

# Para utilizar las cookies del session
app.secret_key = "jBzTos1bzR92pTQ7"


@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@app.route("/index/", methods=['GET', 'POST'])
def index():
    mensaje = ""
    # en session['usuario'] se guarda el expediente del usuario loggeado, por lo que con eso se obtienen todos sus datos
    # se usa el metodo .get() de los diccionarios de python, de modo que si el usuario no está logeado, session['usuario'] == None
    # y el .get() regresará un None y no una excepción
    expediente = session.get('usuario')
    # si se obtuvo un usuario logeado
    if expediente != None:
        # usuario = diccionario_usuarios.get(expediente)
        # Se obtienen los datos del usuario logeado desde la base de datos
        usuario = Usuarios.query.get(expediente)
        # se obtienen sus grupos creados/unidos
        grupos = obtener_grupos(usuario)
    # si el usuario no está logeado
    else:
        # se crean valores por defecto para que el index los pueda procesar
        usuario = Usuarios(expediente='predeterminado', nombre='Invitado', apellido_paterno='Invitado', apellido_materno='Invitado', correo='Invitado@invitado.com', tipo_usuario='Invitado', contrasenia='invitado')
        grupos = []
    if request.method == 'GET':
        return render_template("index.html", usuario=usuario, grupos=grupos, mensaje=mensaje)
    # POST
    else:
        usuario = Usuarios.query.get(expediente)
        # se detecta cual formulario es el que se ha llenado
        # Crear grupo por parte del docente
        if 'crear_grupo' in request.form:
            clave = request.form['clave']
            nombre_grupo = request.form['nombre_grupo']
            descripcion = request.form['descripcion']
            docente_propietario = session['usuario']
            mensaje = crear_grupo_asistencias(clave, nombre_grupo, descripcion, docente_propietario)
            # si el mensaje está vacío es porque el grupo se creó exitosamente
            if mensaje == "":
                # se redirecciona para que se repita todo el proceso de obtener los datos como la variable grupos,
                # la cual se pudo actualizar si el docente creó exitosamente el grupo
                return redirect('/')
            else:
                # si no, se envia el mensaje y se vuelve a renderizar el index
                return render_template('index.html', usuario=usuario, grupos=grupos, mensaje=mensaje)
        # Unirse a un grupo por parte del estudiante (unirse_grupo)
        else:
            clave = request.form['clave']
            mensaje = unirse_grupo_asistencias(clave, usuario)
            # si el mensaje está vacío es porque el estudiante se unió exitosamente
            if mensaje == "":
                # se redirecciona para que se repita todo el proceso de obtener los datos como la variable grupos,
                # la cual se pudo actualizar si el estudiante se unió exitosamente a un grupo
                return redirect('/')
            else:
                # si no, se envia el mensaje y se vuelve a renderizar el index
                return render_template('index.html', usuario=usuario, grupos=grupos, mensaje=mensaje)


@app.route("/sobre_nosotros")
@app.route("/sobre_nosotros/")
def sobre_nosotros():
    return render_template('sobre_nosotros.html')


@app.route('/pagina_no_permitida')
@app.route('/pagina_no_permitida/')
def pagina_no_permitida():
    return render_template('pagina_no_permitida.html')


# para tener una página de error 404 personalizada
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404


# para tener una página de error 500 personalizada
@app.errorhandler(500)
def pagina_error(e):
    return render_template('500.html'), 500