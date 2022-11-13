from flask import Blueprint, render_template, request, session, redirect, jsonify
from Modelos import CodigosQr, IntegrantesGrupos, Usuarios, db, Asistencias
from Usuarios import validar_pertenencia_usuario


asistencias_blueprint = Blueprint('asistencias_blueprint', __name__)


@asistencias_blueprint.route("/asistencias/<clave_grupo>", methods=['GET', 'POST'])
def asistencias(clave_grupo):
    if request.method == "GET":
        usuario = Usuarios.query.get(session['usuario'])
        # se tiene que validar que el usuario que trate de acceder a esta ruta pertenezca o sea el creador del grupo
        pertenece_o_es_creador = validar_pertenencia_usuario(usuario, clave_grupo)
        if pertenece_o_es_creador:
            asistencias = obtener_asistencias(clave_grupo)
            datos_estudiantes = obtener_datos_estudiantes()
            fechas = obtener_fechas_asistencia(clave_grupo)
            return render_template('asistencias.html', asistencias=asistencias, datos_estudiantes=datos_estudiantes, fechas=fechas, usuario=usuario, clave_grupo=clave_grupo)
        else:
            return redirect('/pagina_no_permitida')
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
        return redirect(f'/asistencias/{clave_grupo}')


@asistencias_blueprint.route("/lista_estudiantes/<clave_grupo>", methods=['GET', 'POST'])
def lista_estudiantes(clave_grupo):
    if request.method == "GET":
        usuario = Usuarios.query.get(session['usuario'])
        pertenece_o_es_creador = validar_pertenencia_usuario(usuario, clave_grupo)
        if pertenece_o_es_creador:
            integrantes_grupo_ordenados = obtener_integrantes_grupo_ordenados_por_nombre(clave_grupo)
            return render_template('lista_estudiantes.html', integrantes_grupo=integrantes_grupo_ordenados, usuario=usuario, clave_grupo=clave_grupo)
        else:
            return redirect('/pagina_no_permitida')
    # POST
    else:
        # se obtiene el expediente del estudiante a remover
        expediente_estudiante_a_remover = request.form['expediente_estudiante']
        # se obtienen todos los registros de asistencias que haya tenido ese estudiante en ese grupo determinado
        registros_asistencias_estudiante = Asistencias.query.filter_by(clave_grupo=clave_grupo, expediente_estudiante=expediente_estudiante_a_remover).all()
        for registro in registros_asistencias_estudiante:
            # se van a borrar todos los registros de asistencias de ese estudiante en ese grupo
            db.session.delete(registro)
        # se obtiene el registro en la tabla integrantes_grupos donde se relaciona a ese estudiante con el grupo en el que se ha unido
        integrante = IntegrantesGrupos.query.filter_by(clave_grupo=clave_grupo, expediente_estudiante=expediente_estudiante_a_remover).first()
        db.session.delete(integrante)
        # se actualizan esos borrados en la base de datos
        db.session.commit()
        return redirect(f'/lista_estudiantes/{clave_grupo}')




@asistencias_blueprint.route("/generar_reporte_asistencias/<clave_grupo>", methods=['GET', 'POST'])
def generar_reporte_asistencias(clave_grupo):
    if request.method == "GET":
        usuario = Usuarios.query.get(session['usuario'])
        pertenece_o_es_creador = validar_pertenencia_usuario(usuario, clave_grupo)
        if pertenece_o_es_creador:
            fechas = obtener_fechas_asistencia(clave_grupo)
            estudiantes = obtener_integrantes_grupo_ordenados_por_nombre(clave_grupo)
            return render_template('reporte_asistencias.html', clave_grupo=clave_grupo, fechas=fechas, estudiantes=estudiantes, usuario=usuario)
        else:
            return redirect('/pagina_no_permitida')


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
    Se regresan todas las fechas en orden ascendente de un grupo de asistencias en el que se ha tomado asistencias, al haberse generado un código QR.
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


def obtener_integrantes_grupo_ordenados_por_nombre(clave_grupo: str) -> list:
    """
    Regresa un listado ordenado (por apellido paterno) de estudiantes que integran a un grupo dado.
    """
    datos_estudiantes = obtener_datos_estudiantes()
    integrantes_grupo = IntegrantesGrupos.query.filter_by(clave_grupo=clave_grupo).all()
    lista_integrantes_grupo = []
    # aquí se relaciona a los integrantes del grupo con sus datos de la tabla de Usuarios obtenidos anteriormente
    for integrante in integrantes_grupo:
        expediente_estudiante = integrante.expediente_estudiante
        datos_integrante = datos_estudiantes[expediente_estudiante]
        apellido_paterno_integrante = datos_integrante['apellido_paterno']
        apellido_materno_integrante = datos_integrante['apellido_materno']
        nombre_integrante = datos_integrante['nombre']
        lista_integrantes_grupo.append({'expediente': expediente_estudiante, 'nombre_completo': f'{apellido_paterno_integrante} {apellido_materno_integrante} {nombre_integrante}'})
    # aquí se ordena a los estudiantes de manera ascendente por el nombre completo
    # se le aplica el metodo de upper a cada nombre completo para pasar todos los caracteres a mayusculas, esto es porque por ejemplo
    # si un usuario se apellida Reyes y otro Juarez, si los ordena correctamente, pero si el usuario puso su
    # apellido paterno en minusculas, ejemplo Reyes y juarez, pone primero al usuario Reyes y luego a juarez
    # esto puede deberse a que al compararse los strings y ver cual es mayor, el primer caracter en mayuscula y minuscula
    # sea mayor
    lista_integrantes_grupo_ordenada = sorted(lista_integrantes_grupo, key=lambda item: item.get('nombre_completo').upper())
    return lista_integrantes_grupo_ordenada


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
    # tambien se obtienen a los estudiantes que se hayan unido a ese grupo, esto va  a servir para ver que estudiantes no registraron asistencia un cierto dia y asignarles el estado correspondiente (falta), sin tener que insertar en la bd, 
    # de modo que se ahorra espacio en la bd
    lista_integrantes_grupo_ordenada = obtener_integrantes_grupo_ordenados_por_nombre(clave_grupo)
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


def obtener_cantidad_estudiantes_grupo(clave_grupo: str) -> int:
    cantidad_estudiantes = 0
    integrantes = IntegrantesGrupos.query.filter_by(clave_grupo=clave_grupo).all()
    if integrantes is not None:
        cantidad_estudiantes = len(integrantes)
    return cantidad_estudiantes


@asistencias_blueprint.route("/datos_reporte_asistencias/<clave_grupo>/<expediente_estudiante>")
def datos_reporte_asistencias(clave_grupo, expediente_estudiante):
    '''
    En esta ruta se va a generar un JSON con la siguiente forma:
    {
        '2022-11-06': {
            'asistencias': 32,
            'retardos': 4,
            'faltas': 4
        },
        '2022-11-07': {
            'asistencias': 34,
            'retardos': 3,
            'faltas': 3
        },...
    }
    Este diccionario/objeto va a ser utilizado para generar las graficas en el reporte de asistencias
    '''
    # se obtienen todas las fechas ordenadas en las que se haya generado un codigo qr para tomar asistencia
    fechas = obtener_fechas_asistencia(clave_grupo)
    # se obtiene la cantidad de estudiantes en un grupo (este dato va  a servir para determinar las faltas que no se registran en la base de datos al no escanearse el codigo qr en una fecha dada)
    cantidad_estudiantes = obtener_cantidad_estudiantes_grupo(clave_grupo)
    # con una compresion de diccionarios, se genera la estructura planteada con todos los valores inicializados en 0.
    # de igual modo las fechas se toman de las fechas registradas en la generacion de los codigos qr, de modo que si
    # en algun dia, ningun estudiante escaneo el codigo qr, de modo que en asistencias no haya ningun registro en esa fecha
    # no va a haber problema, por que esa fecha va a ser obtenida de la generacion del codigo qr y se les va a asignar falta a todos por defecto
    datos_reporte_asistencias = {fecha: {'asistencias': 0, 'retardos': 0, 'faltas': 0} for fecha in fechas}
    # en la base de datos los estados de asistencia se guardan como 'Asistencia', 'Retardo' y 'Falta', 
    # por lo que aqui se relacionan con su sustantivo en plural, para que el JSON quede mas entendible
    sustantivo_plural = {'Asistencia': 'asistencias', 'Retardo': 'retardos', 'Falta': 'faltas'}
    # se tiene que checar si se busca generar un reporte de asistencias para todos los integrantes del grupo
    # o si es para un estudiante en especifico
    if expediente_estudiante == 'Todos':
        # si es para todos, no se filtra por el expediente del estudiante
        # los registros de asistencias se ordenan por fecha ascendente para asegurarnos de que sigan ordenadas
        datos_asistencias = Asistencias.query.filter_by(clave_grupo=clave_grupo).order_by(Asistencias.fecha.asc()).all()
    else:
        # se valida si el usuario no es integrante en el grupo
        integrante = IntegrantesGrupos.query.filter_by(clave_grupo=clave_grupo, expediente_estudiante=expediente_estudiante).first()
        if integrante is None:
            return jsonify({})
        # de otro modo se filtra por el expediente del estudiante ademas de la clave del grupo en concreto
        datos_asistencias = Asistencias.query.filter_by(clave_grupo=clave_grupo, expediente_estudiante=expediente_estudiante).order_by(Asistencias.fecha.asc()).all()
    # se recorre cada registro en la tabla Asistencias filtrada
    for registro_asistencia in datos_asistencias:
        # se obtiene el campo de fecha convertido a string
        fecha = str(registro_asistencia.fecha)
        # se obtiene el estado de asistencia equivalente a su sustantivo plural
        # si el estado de asistencia obtenido en el registro es 'Retardo', entonces:
        # estado_asistencia = sustantivo_plural['Retardo'] = 'retardos'
        estado_asistencia = sustantivo_plural[registro_asistencia.estado]
        # se incrementa en uno el estado de asistencia que se haya obtenido
        datos_reporte_asistencias[fecha][estado_asistencia] = datos_reporte_asistencias[fecha][estado_asistencia] + 1
    # ahora como en la base de datos no se guardan aquellos registros de faltas cuando los estudiantes no escanearon el codigo qr en todo ese dia,
    # se tienen que tomar en cuenta esas faltas "no registradas", por lo que se recorre el diccionario
    for fecha, estados_asistencias in datos_reporte_asistencias.items():
        # por cada fecha se suman todas las cantidades de estados de asistencias registrados en la base de datos
        cantidad_estados_asistencias_registrados = estados_asistencias['asistencias'] + estados_asistencias['retardos'] + estados_asistencias['faltas']
        # se tiene que checar si el reporte es para todos los estudiantes del grupo o para un estudiante en especifico
        if expediente_estudiante == 'Todos':
            # las faltas no registradas se obtienen al restarle a la cantidad de estudiantes en un grupo, la cantidad de estados de asistencias registrados
            faltas_no_registradas = cantidad_estudiantes - cantidad_estados_asistencias_registrados
        else:
            # si es para un estudiante en especifico, se puede checar si no registro una asistencia en una fecha dada
            # al ver si en una fecha dada la cantidad_estados_asistencias_registrados es 0, lo que quiere decir que no registro ningun estado
            # si cantidad_estados_asistencias_registrados es mayor a 0 es porque registro asistencia esa fecha, 
            # por lo que faltas_no_registradas = 0
            faltas_no_registradas = 0
            if cantidad_estados_asistencias_registrados == 0:
                # si no registro asistencia esa fecha, es porque tiene una falta no registrada
                faltas_no_registradas = 1
        # esas faltas no registradas se suman a las faltas registradas
        datos_reporte_asistencias[fecha]['faltas'] = datos_reporte_asistencias[fecha]['faltas'] + faltas_no_registradas
    # se regresa el diccionario en forma de JSON
    return jsonify(datos_reporte_asistencias)