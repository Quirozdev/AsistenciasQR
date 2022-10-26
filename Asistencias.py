from flask import Blueprint, render_template, request, session, redirect
from Modelos import CodigosQr, IntegrantesGrupos, Usuarios, db, Asistencias


asistencias_blueprint = Blueprint('asistencias_blueprint', __name__)


@asistencias_blueprint.route("/asistencias/<clave_grupo>", methods=['GET', 'POST'])
def asistencias(clave_grupo):
    if request.method == "GET":
        asistencias = obtener_asistencias(clave_grupo)
        datos_estudiantes = obtener_datos_estudiantes()
        fechas = obtener_fechas_asistencia(clave_grupo)
        usuario = Usuarios.query.get(session['usuario'])
        return render_template('asistencias.html', asistencias=asistencias, datos_estudiantes=datos_estudiantes, fechas=fechas, usuario=usuario, clave_grupo=clave_grupo)
    # POST
    else:
        # en asistencias.html hay un fragmento de codigo de JavaScript que contiene una funcion que se encuentra
        # enlazada a todos los select que se generan dinamicamente, cuando hay un cambio de opcion en estos
        # select, se invoca la funcion, la cual obtiene el atributo nombre (name) del select que se genera 
        # dinamicamente con el expediente del estudiante (fila) y la fecha (columna), ademas de obtener el valor
        # del select al elegir otra opcion (asistencia, retardo, falta), ahi mismo se crea un formulario invisible
        # que tiene un input dentro con un valor que contiene expediente, fecha y estado de asistencia, y que se manda
        # esa informacion mediante un POST a esta pagina.
        # aqui se obtiene ese valor que contiene los 3 valores mencionados anteriormente
        datos_asistencia = request.form['datos_asistencia']
        # los datos vienen en la forma: expediente_estudiante fecha estado_asistencia, separados por un espacio en blanco
        # por lo que se obtienen individualmente (en el registro expediente_estudiante no puede contener espacios en blancos para evitar problemas aqui)
        datos_asistencia_lista = datos_asistencia.split(" ")
        expediente_estudiante = datos_asistencia_lista[0]
        fecha = datos_asistencia_lista[1]
        # se le aplica el metodo de .title() para que ponga en mayuscula el primer caracter, porque el formulario regresa
        # los datos en minusculas (asistencia, retardo, falta) y se busca -> (Asistencia, Retardo, Falta)
        estado_asistencia = datos_asistencia_lista[2].title()
        # se obtiene el registro correspondiente y se modifica el campo de estado de asistencia
        registro_asistencia = Asistencias.query.filter_by(expediente_estudiante=expediente_estudiante, clave_grupo=clave_grupo, fecha=fecha).first()
        print(registro_asistencia)
        # es posible que el usuario no haya registrado su asistencia esa fecha en el grupo dado y como en la base de datos
        # no se guardan las faltas (para ahorrar espacio en la bd) que se generan automaticamente con la funcion obtener_asistencias()
        # entonces hay que checar si se obtuvo el registro o no.
        # si no se obtuvo, se crea y se inserta
        if registro_asistencia is None:
            # si no se obtuvo un registro, se crea
            registro_asistencia = Asistencias(fecha=fecha, estado=estado_asistencia, expediente_estudiante=expediente_estudiante, clave_grupo=clave_grupo)
            db.session.add(registro_asistencia)
            db.session.commit()
        # si se obtuvo, se actualiza el registro
        else:
            registro_asistencia.estado = estado_asistencia
            # se actualiza el registro
            db.session.commit()
        print(datos_asistencia_lista)
        return redirect(f'/asistencias/{clave_grupo}')

def obtener_datos_estudiantes() -> dict:
    """
    Regresa un diccionario que como llaves tiene los expedientes de los estudiantes y como valores algunos datos (nombre, apellido paterno y materno) del correspondiente estudiante.
    """
    datos_estudiantes = {}
    estudiantes = Usuarios.query.filter_by(tipo_usuario='Estudiante').all()
    for estudiante in estudiantes:
        datos_estudiantes[estudiante.expediente] = {'nombre': estudiante.nombre, 'apellido_paterno': estudiante.apellido_paterno, 'apellido_materno': estudiante.apellido_materno} 
    return datos_estudiantes


def obtener_fechas_asistencia(clave_grupo: str) -> list:
    """
    Se regresan todas las fechas de un grupo de asistencias en el que se ha tomado asistencias, al haberse generado un código QR.
    """
    # se obtienen todas las codigos qr generados del grupo dado, se ordena la query por la fecha de manera ascendente.
    codigos_qr = CodigosQr.query.filter_by(clave_grupo=clave_grupo).order_by(CodigosQr.fecha.asc()).all()
    # las fechas no se obtienen de la tabla de asistencias, porque puede darse el caso de que se genere un codigo QR para
    # un dia y cuando no se han registrado asistencias, entonces la tabla de asistencias no contiene esa fecha hasta que alguien registre
    # una asistencia. Como cada día solo se podrá generar un código QR por grupo, la fecha de las asistencias se relaciona.
    # De igual modo como cada grupo solo puede generar un código QR cada día, no se obtienen fechas repetidas
    fechas = []
    for codigo_qr in codigos_qr:
        # se transforma la fecha a su formato string, porque directamente se obtiene un objeto datetime.datetime.date()
        fecha_str = f'{codigo_qr.fecha}'
        fechas.append(fecha_str)
    return fechas


def obtener_asistencias(clave_grupo:str) -> dict:
    """
    Regresa un diccionario que como llaves tiene los expedientes de los estudiantes integrantes del
    grupo dado y como valores diccionarios que relacionan la fecha con su estado de asistencia.
    """
    # se obtienen todos los registros de asistencias del grupo dado de la tabla correspondiente
    asistencias = Asistencias.query.filter_by(clave_grupo=clave_grupo).all()
    # este diccionario es "incompleto" porque le va a faltar contener los registros que no se guardan en la bd
    # de aquellos estudiantes que no hayan escaneado un código QR en una fecha dada, por lo que no se registra nada
    # de ellos en la fecha correspondiente.
    # Este diccionario va a contener los registros disponibles y los que faltan mencionados anteriormente, se 
    # generarán más adelante.
    # como llaves tendrá las fechas de asistencias registradas y como valor un diccionario que relaciona el expediente de un estudiante, con su estado
    # de asistencia en esa fecha correspondiente.
    diccionario_asistencias_incompleto = {}
    for asistencia in asistencias:
        expediente_estudiante = asistencia.expediente_estudiante
        fecha = asistencia.fecha
        fecha_str = f'{fecha}'
        # si aún no se ha agregado esa fecha al diccionario como llave
        if fecha_str not in diccionario_asistencias_incompleto:
            # se crea un nuevo diccionario como valor
            diccionario_asistencias_incompleto[fecha_str] = {expediente_estudiante: asistencia.estado}
        else:
            # de otro modo, se actualiza el diccionario que está como valor para incluir los datos de asistencia de otro estudiante para esa fecha
            diccionario_asistencias_incompleto[fecha_str].update({expediente_estudiante: asistencia.estado})
    # se obtienen a todos los estudiantes, esto para relacionar sus datos con los integrantes/estudiantes pertenecientes al grupo
    # se hace esta sola query y luego se relaciona mediante un ciclo, para no estar realizando una query dentro del ciclo por cada usuario
    # lo que podria ser pesado para la base de datos
    estudiantes = Usuarios.query.filter_by(tipo_usuario='Estudiante').all()
    diccionario_estudiantes = {}
    for estudiante in estudiantes:
        # el diccionario tiene como llave el expediente de los estudiantes y como valor el nombre completo de estos mismos empezando por el apellido paterno.
        # Esto es así para poder ordenar a los estudiantes por su nombre en la tabla que se generará en asistencias.html
        diccionario_estudiantes[estudiante.expediente] = f'{estudiante.apellido_paterno} {estudiante.apellido_materno} {estudiante.nombre}'
    # tambien se obtienen a los estudiantes que se hayan unido a ese grupo, esto va  a servir para ver que estudiantes no registraron asistencia un cierto dia y asignarles el estado correspondiente (falta), sin tener que insertar en la bd, 
    # de modo que se ahorra espacio en la bd
    integrantes_grupo = IntegrantesGrupos.query.filter_by(clave_grupo=clave_grupo).all()
    lista_integrantes_grupo = []
    # aquí se relaciona a los integrantes del grupo con sus datos de la tabla de Usuarios obtenidos anteriormente
    for integrante in integrantes_grupo:
        expediente_estudiante = integrante.expediente_estudiante
        lista_integrantes_grupo.append({'expediente': expediente_estudiante, 'nombre_completo': diccionario_estudiantes[expediente_estudiante]})
    # aquí se ordena a los estudiantes de manera ascendente por el nombre completo
    lista_integrantes_grupo_ordenada = sorted(lista_integrantes_grupo, key=lambda item: item.get('nombre_completo'))
    # se obtienen las fechas registradas, donde se haya generado un código QR
    fechas = obtener_fechas_asistencia(clave_grupo)
    # este diccionario va a complementar los registros que el diccionario_asistencias_incompleto no tenía, por que 
    # no se guardan los registros de los estudiantes que no registren asistencia, por lo que se les va a asignar Falta como estado de asistencia.
    # Se hace de esta manera para evitar el realizar queries dentro del ciclo que pueden provocar mucho trabajo por parte de la bd.
    diccionario_asistencias_completo = {}
    for integrante in lista_integrantes_grupo_ordenada:
        expediente_estudiante = integrante['expediente']
        # este diccionario va a ser el valordel diccionario completo, va a contener como llave la fecha y como valor el estado de asistencia.
        diccionario_fecha_estado = {}
        for fecha in fechas:
            # si la fecha no está en el diccionario de asistencias incompleto, es porque se generó un código QR para esa fecha
            # pero nadié registro asistencia
            if fecha not in diccionario_asistencias_incompleto:
                estado_asistencia = "Falta"
            # si el estudiante no registró asistencia en una fecha dada, de igual modo se le va a asignar falta
            elif expediente_estudiante not in diccionario_asistencias_incompleto[fecha]:
                estado_asistencia = "Falta"
            # si se encontró fecha y el expediente del estudiante se encuentra registrado en esa fecha, entonces se obtiene su estado de asistencia.
            else:
                estado_asistencia = diccionario_asistencias_incompleto.get(fecha).get(expediente_estudiante)
            diccionario_fecha_estado[fecha] = estado_asistencia
        diccionario_asistencias_completo[expediente_estudiante] = diccionario_fecha_estado
    return diccionario_asistencias_completo
    


def obtener_estado_asistencia(hora_registro, hora_asistencia, hora_retardo) -> str:
    """
    Regresa el estado de asistencia (asistencia, retardo, falta) dependiendo de la hora en la que el
    estudiante escaneó el código QR y las horas límites establecidas por el codigo QR.
    """
    estado_asistencia = ""
    if hora_registro > hora_retardo:
        estado_asistencia = "Falta"
    elif hora_registro > hora_asistencia:
        estado_asistencia = "Retardo"
    else:
        estado_asistencia = "Asistencia"
    return estado_asistencia