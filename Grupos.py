from flask import Blueprint, render_template, session, redirect, request
from Modelos import CodigosQr, db, IntegrantesGrupos, Grupos, Usuarios, Asistencias
from Otros import obtener_fecha_actual
from Usuarios import validar_pertenencia_usuario


grupos_blueprint = Blueprint('grupos_blueprint', __name__)


@grupos_blueprint.route("/grupo/<clave_grupo>")
def grupos(clave_grupo):
    usuario = Usuarios.query.get(session['usuario'])
    pertenece_o_es_creador = validar_pertenencia_usuario(usuario, clave_grupo)
    if pertenece_o_es_creador:
        grupo = Grupos.query.get(clave_grupo)
        fecha_actual = obtener_fecha_actual().date()
        # se obtiene el codigo qr que se haya generado el dia actual en ese grupo, si es que se ha generado alguno
        codigo_qr_hoy = CodigosQr.query.filter_by(fecha=fecha_actual, clave_grupo=clave_grupo).first()
        # esto es para ver el estado de asistencia del estudiante
        asistencia = Asistencias.query.filter_by(fecha=fecha_actual, expediente_estudiante=usuario.expediente, clave_grupo=clave_grupo).first()
        if asistencia is None:
            estado_asistencia = "Desconocido"
        else:
            estado_asistencia = asistencia.estado
        return render_template('grupo.html', usuario=usuario, grupo=grupo, codigo_qr_hoy=codigo_qr_hoy, fecha=fecha_actual, estado_asistencia=estado_asistencia)
    else:
        return redirect('/pagina_no_permitida')


@grupos_blueprint.route("/modificar_grupo/<clave_grupo>", methods=['GET', 'POST'])
def modificar_grupo(clave_grupo):
    usuario = Usuarios.query.get(session['usuario'])
    grupo = Grupos.query.get(clave_grupo)
    if request.method == "GET":
        mensaje = ""
        # se valida que el usuario que esta tratando de acceder a esa ruta sea el docente propietario del grupo
        if grupo.expediente_propietario == usuario.expediente:
            return render_template('modificar_grupo.html', grupo=grupo, mensaje=mensaje)
        else:
            return redirect('/pagina_no_permitida')
    # POST
    else:
        # se obtienen los datos del formulario, la clave del grupo es inalterable por ser llave primaria
        clave_grupo = request.form['clave_grupo']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        # se actualiza el registro
        grupo.nombre = nombre
        grupo.descripcion = descripcion
        # se guardan los cambios
        db.session.commit()
        # se redirecciona a la pagina de ese grupo
        return redirect(f'/grupo/{clave_grupo}')

def obtener_grupos(usuario: object) -> list:
    """
    Se obtienen los grupos de un usuario dado ya sea los que posee un docente o en los que se ha unido un estudiante
    """
    grupos = []
    tipo_usuario = usuario.tipo_usuario
    expediente = usuario.expediente
    if tipo_usuario == "Estudiante":
        # se obtienen las claves de los grupos a los que se ha unido ese estudiante
        claves_grupos = IntegrantesGrupos.query.filter_by(expediente_estudiante=expediente).all()
        for grupo in claves_grupos:
            # se relacionan la tabla integrantes_grupos y grupos y se van obteniendo los grupos mediante la 
            # llave foranea de integrantes_grupos
            grupo_info_extra = Grupos.query.get(grupo.clave_grupo)
            # tambien se van a agregar los atributos del docente propietario, que seran mostrados en el index
            docente_propietario = Usuarios.query.get(grupo_info_extra.expediente_propietario)
            grupo_info_extra.nombre_propietario = docente_propietario.nombre
            grupo_info_extra.apellido_paterno_propietario = docente_propietario.apellido_paterno
            grupo_info_extra.apellido_materno_propietario = docente_propietario.apellido_materno
            grupos.append(grupo_info_extra)
    # Docente
    else:
        # se obtienen los grupos que el docente haya creado, filtrando los grupos que pertenezcan a su expediente
        grupos = Grupos.query.filter_by(expediente_propietario=expediente).all()
    return grupos


def crear_grupo_asistencias(clave_grupo: str, nombre_grupo: str, descripcion: str, expediente_docente: str) -> str:
    """
    Le permite al mastro crear un grupo de asistencias, regresa un string no vacío si 
    surgió un error en el proceso, en caso contrario regresa un string vacío.
    """
    mensaje = ""
    grupo = Grupos.query.get(clave_grupo)
    # si ya hay un grupo con esa clave (si se obtuvo un resultado de la query es porque ya existe un grupo de
    # asistencias con esa clave, por lo que es no None)
    if grupo is not None:
        mensaje = "Ya hay un grupo de asistencias con esa clave, intenta con otra"
    else:
        # se crea el objeto/fila Grupo
        grupo_nuevo = Grupos(clave=clave_grupo, nombre=nombre_grupo, descripcion=descripcion, expediente_propietario=expediente_docente)
        db.session.add(grupo_nuevo)
        # se insertan los cambios
        db.session.commit()
    return mensaje


def unirse_grupo_asistencias(clave_grupo: str, estudiante: object) -> str:
    """
    Le permite al estudiante unirse a un grupo de asistencias, regresa un string no vacío si 
    surgió un error en el proceso, en caso contrario regresa un string vacío.
    """
    mensaje = ""
    # se obtiene el grupo al que se quiere unir el estudiante
    grupo = Grupos.query.get(clave_grupo)
    # se checa si la clave ingresada corresponde a un grupo existente
    if grupo is not None:
        # se obtienen todos los grupos a los que se ha unido ese estudiante
        grupos_accedidos = IntegrantesGrupos.query.filter_by(expediente_estudiante=estudiante.expediente).all()
        # se valida que el estudiante no haya accedido ya al grupo de asistencias que busca unirse
        for grupo_accedido in grupos_accedidos:
            # se checa si el grupo y el estudiante ya están relacionados, por lo que si lo están, quiere decir que el estudiante ya se ha unido a ese grupo de asistencias
            if grupo_accedido.clave_grupo == grupo.clave:
                mensaje = "Ya eres miembro de ese grupo de asistencias"
                return mensaje
        # si no se ha unido a ese grupo de asistencias
        # se crea el nuevo registro
        integrante_grupo = IntegrantesGrupos(clave_grupo=clave_grupo, expediente_estudiante=estudiante.expediente)
        db.session.add(integrante_grupo)
        # se insertan los cambios
        db.session.commit()
    else:
        mensaje = "No hay ningun grupo de asistencias con esa clave"
    return mensaje