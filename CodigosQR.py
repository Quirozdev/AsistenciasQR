from flask import Blueprint, render_template, session, request, redirect
from Modelos import Asistencias, db, IntegrantesGrupos, Grupos, Usuarios, CodigosQr
from Asistencias import obtener_estado_asistencia
from Otros import convertir_str_a_hora, obtener_fecha_actual
from Usuarios import validar_pertenencia_usuario


codigos_qr_blueprint = Blueprint('codigos_qr_blueprint', __name__)


@codigos_qr_blueprint.route("/generar_qr/<clave_grupo>", methods=['GET', 'POST'])
def generar_qr(clave_grupo):
    mensaje = ""
    usuario = Usuarios.query.get(session['usuario'])
    if request.method == 'GET':
        pertenece_o_es_creador = validar_pertenencia_usuario(usuario, clave_grupo)
        if pertenece_o_es_creador:
            return render_template('generarQR.html', mensaje=mensaje, usuario=usuario)
        else:
            return redirect('/pagina_no_permitida')
    # POST
    else:
        # se obtienen los datos
        clave_codigo_qr = request.form['clave']
        # se verifica que esa clave del codigo qr no haya sido usada
        codigo_qr = CodigosQr.query.get(clave_codigo_qr)
        if codigo_qr is not None:
            mensaje = "Esa clave ya ha sido utilizada, intenta con otra."
            return render_template('generarQR.html', mensaje=mensaje, usuario=usuario)
        # se obtiene la fecha actual en formato YYYY/MM/DD
        fecha = obtener_fecha_actual().date()
        # se valida tambien que no se haya generado un codigo qr para ese dia (esto es por si el usuario ingresa a la pagina de generar qr desde la barra de navegacion, porque en la pagina de grupo el boton de generar qr no aparece cuando ya hay un codigo qr generado para ese dia)
        codigo_qr_actual = CodigosQr.query.filter_by(clave_grupo=clave_grupo, fecha=fecha).first()
        if codigo_qr_actual is not None:
            mensaje = f"Ya se ha generado un código QR para el día de hoy {fecha}"
            return render_template('generarQR.html', mensaje=mensaje, usuario=usuario)
        # se obtienen las horas y se transforman a un objeto hora para poder procesarlo y validar la condicion que viene despues
        hora_inicio = convertir_str_a_hora(request.form['hora_inicio'])
        hora_asistencia = convertir_str_a_hora(request.form['hora_asistencia'])
        hora_retardo = convertir_str_a_hora(request.form['hora_retardo'])
        # se valida que las horas sigan un orden logico, por ejemplo no es posible que la hora limite de asistencia sea mayor que la hora limite de retardo
        if not (hora_inicio < hora_asistencia < hora_retardo):
            mensaje = "Las horas deben de seguir el orden de hora de inicio < hora límite de asistencia < hora límite de retardo."
            return render_template('generarQR.html', mensaje=mensaje, usuario=usuario)
        clave_grupo = clave_grupo
        nuevo_codigo_qr = CodigosQr(clave=clave_codigo_qr, hora_inicio=hora_inicio, hora_asistencia=hora_asistencia, hora_retardo=hora_retardo, fecha=fecha, clave_grupo=clave_grupo)
        db.session.add(nuevo_codigo_qr)
        # se inserta el nuevo codigo qr en la bd
        db.session.commit()
        # se redirecciona a la pagina del grupo
        return redirect(f'/grupo/{clave_grupo}')


@codigos_qr_blueprint.route("/escanear_qr/<clave_grupo>", methods=['GET', 'POST'])
def escanear_qr(clave_grupo):
    mensaje = ""
    usuario = Usuarios.query.get(session['usuario'])
    if request.method == 'GET':
        pertenece_o_es_creador = validar_pertenencia_usuario(usuario, clave_grupo)
        if pertenece_o_es_creador:
            return render_template('escanearQR.html', mensaje=mensaje, usuario=usuario)
        else:
            return redirect('/pagina_no_permitida')
    # POST
    else:
        # se obtiene la hora y la fecha a la que registro su asistencia el usuario
        hora_registro = convertir_str_a_hora(obtener_fecha_actual().strftime("%H:%M"))
        fecha = obtener_fecha_actual().date()
        clave_codigo_qr = request.form['clave']
        # se obtiene al registro del codigo qr con la clave, grupo y fecha dados
        codigo_qr = CodigosQr.query.filter_by(clave=clave_codigo_qr, clave_grupo=clave_grupo, fecha=fecha).first()
        # si no se encontró ese código qr en la base de datos
        if codigo_qr is None:
            mensaje = "El Código QR no es válido, no ha sido generado para este grupo o ya ha expirado"
            return render_template('escanearQR.html', mensaje=mensaje, usuario=usuario)
        # tambien se tiene que validar que el usuario no haya registrado ya su asistencia para ese dia
        asistencia = Asistencias.query.filter_by(expediente_estudiante=session['usuario'], clave_grupo=clave_grupo, fecha=fecha).first()
        if asistencia is not None:
            mensaje = f"Ya has registrado tu asistencia en este grupo el día de hoy ({fecha})"
            return render_template('escanearQR.html', mensaje=mensaje, usuario=usuario)
        # de igual forma se valida que el usuario no escanee el codigo qr antes de que se haya iniciado (hora_inicio)
        hora_inicio = codigo_qr.hora_inicio
        if hora_inicio > hora_registro:
            mensaje = f"Aún no puedes registrar tu asistencia, espera hasta las {hora_inicio}"
            return render_template('escanearQR.html', mensaje=mensaje, usuario=usuario)
        # si se encontro el codigo qr en la bd, se valido que no haya registrado ya su asistencia y se haya validado que la hora de registro sea mayor a la hora de inico del codigo qr
        # se calcula el estado de asistencia (asistencia, retardo o falta)
        hora_asistencia = codigo_qr.hora_asistencia
        hora_retardo = codigo_qr.hora_retardo
        estado_asistencia = obtener_estado_asistencia(hora_registro, hora_asistencia, hora_retardo)
        # se registra la asistencia en la bd
        asistencia_nueva = Asistencias(fecha=fecha, estado=estado_asistencia, expediente_estudiante=session['usuario'], clave_grupo=clave_grupo)
        db.session.add(asistencia_nueva)
        # se insertan la asistencia
        db.session.commit()
        # se redirecciona a la pagina grupo
        return redirect(f'/grupo/{clave_grupo}')