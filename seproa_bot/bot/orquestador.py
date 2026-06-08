# bot/orquestador.py
from bot.detectores import (
    detectar_ataque_inyeccion,
    detectar_intencion_transaccional,
    detectar_intencion_ubicacion,
    detectar_saludo,
    detectar_despedida
)
from services.openai_service import obtener_respuesta_ia_optimizada
from services.openai_reserva_service import obtener_extraccion_ia
import services.openai_service as openai_cache # Para acceder a las variables globales
from datetime import datetime, date
from services.google_calendar_service import verificar_disponibilidad, agendar_cita_google
from services.email_service import enviar_correo_confirmacion

# Nuevos imports para apagar vacaciones
from db.database import SessionLocal
from db.models import ConfiguracionBot, HorarioAtencion

# Limpiador de emojis para respuestas de IA cuando el uso de emojis está desactivado en la configuración
def limpiar_emojis(texto: str) -> str:
    usa_emojis = getattr(openai_cache, 'USA_EMOJIS_CACHED', True)
    if not usa_emojis:
        emojis = ["📅", "📧", "📋", "🔹", "⏰", "✅", "🎉", "🚨", "🛑", "👋", "🗺️", "📍", "🤝", "🧠", "🏖️"]
        for e in emojis:
            texto = texto.replace(e, "")
    return texto

async def procesar_intencion(texto_usuario: str, historial: list, es_nuevo_usuario: bool, chat_id: str, estado_actual: str) -> tuple[str, str, dict, str]:
    """
    Evalúa la intención del usuario y decide qué motor usar.
    Retorna: (texto_de_respuesta, accion_especial, datos_json, nuevo_estado)
    """
    texto_limpio = texto_usuario.lower()

    # 0. DETECCIÓN DE ATAQUES DE INYECCIÓN
    if detectar_ataque_inyeccion(texto_usuario):
        return "Lo siento, por políticas de seguridad de SEPROA no puedo procesar esa solicitud.", None, None, estado_actual

    # 0.1 Detectar vacaciones (Caché RAM)
    vacaciones_activas = getattr(openai_cache, 'VACACIONES_ACTIVAS_CACHED', False)
    fecha_regreso = getattr(openai_cache, 'FECHA_REGRESO_CACHED', None)

    if vacaciones_activas and fecha_regreso:
        if date.today() >= fecha_regreso:
            # Apagado automático de vacaciones (Sesión local rápida)
            db = SessionLocal()
            try:
                config = db.query(ConfiguracionBot).first()
                if config:
                    config.modo_vacaciones = False; config.fecha_regreso = None; db.commit()
                openai_cache.VACACIONES_ACTIVAS_CACHED = False; openai_cache.FECHA_REGRESO_CACHED = None
            finally: db.close()
        else:
            mensaje_vac = f"Gracias por contactarnos. Actualmente la empresa se encuentra cerrada. 🏖️ Regresamos el {fecha_regreso.strftime('%d/%m/%Y')}."
            return limpiar_emojis(mensaje_vac), None, None, "NORMAL"

    if es_nuevo_usuario:
        return openai_cache.MENSAJE_SALUDO_CACHED, None, None, "NORMAL"

    ultimo_mensaje_bot = ""
    if historial:
        for msg in reversed(historial):
            if msg["role"] == "assistant":
                ultimo_mensaje_bot = msg["content"].lower(); break

    # 1. MÁQUINA DE ESTADOS (AGENDANDO)
    if estado_actual == "AGENDANDO" or detectar_intencion_transaccional(texto_usuario, ultimo_mensaje_bot):
        horarios_disponibles = getattr(openai_cache, 'HORARIOS_TEXTO_CACHED', 'Lunes a Viernes de 9:00 a 15:00')
        nombres_servicios = getattr(openai_cache, 'NOMBRES_SERVICIOS_CACHED', ["General"])

        # --- LLAMADA EXTERNA (DB LIBRE) ---
        datos = await obtener_extraccion_ia(historial, horarios_disponibles, nombres_servicios)

        intencion = datos.get("intencion"); servicio = datos.get("servicio_detectado", "General")
        fecha = datos.get("fecha"); email = datos.get("email"); hora = datos.get("hora")
        confirmado = datos.get("confirmacion_final", False)

        if intencion == "solo_informacion" and estado_actual != "AGENDANDO":
            resp_info = await obtener_respuesta_ia_optimizada(historial)
            # Limpiar etiqueta si la IA la incluyó por error
            resp_info = resp_info.replace("[ACTIVAR_AGENDA]", "").replace("ACTIVAR_AGENDA", "").strip()
            return limpiar_emojis(resp_info), "actualizar_clasificacion", datos, "NORMAL"

        # Validaciones de tiempo (DB Local Rápida)
        fecha_invalida = not fecha or str(fecha).lower() in ["null", "none", ""]
        hora_invalida = not hora or str(hora).lower() in ["null", "none", ""]

        if not fecha_invalida:
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
                dias = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
                nombre_dia = dias[fecha_obj.weekday()]

                db = SessionLocal()
                try:
                    horario_dia = db.query(HorarioAtencion).filter(HorarioAtencion.dia_semana == nombre_dia).first()
                    if not horario_dia or not horario_dia.es_laboral:
                        fecha_invalida = True
                    elif not hora_invalida:
                        h_int = int(str(hora).split(":")[0])
                        if h_int < horario_dia.hora_inicio.hour or h_int >= horario_dia.hora_fin.hour:
                            hora_invalida = True
                finally: db.close()
            except: fecha_invalida = True

        if fecha_invalida or hora_invalida:
            res_f = f"Para agendar tu cita de {servicio}, necesito fecha y hora exacta. 📅\n\nHorarios: {horarios_disponibles}\n¿Qué día prefieres?"
            return limpiar_emojis(res_f), "actualizar_clasificacion", datos, "AGENDANDO"

        # --- LLAMADA EXTERNA (DB LIBRE) ---
        if not await verificar_disponibilidad(fecha, hora):
            return limpiar_emojis(f"Lo lamento, el {fecha} a las {hora} ya está reservado. 📅 ¿Otro horario?"), "actualizar_clasificacion", datos, "AGENDANDO"

        if not email:
            return limpiar_emojis(f"¡Espacio libre el {fecha} {hora}! 📧 ¿Cuál es tu correo para la invitación?"), "actualizar_clasificacion", datos, "AGENDANDO"

        if not confirmado:
            res_c = f"📋 **RESUMEN**\n🔹 Servicio: {servicio}\n📅 Fecha: {fecha}\n⏰ Hora: {hora}\n📧 Correo: {email}\n\n¿Es correcto? Responde **'Sí'**."
            return limpiar_emojis(res_c), "actualizar_clasificacion", datos, "AGENDANDO"

        # --- AGENDAMIENTO FINAL (DB LIBRE) ---
        google_id = await agendar_cita_google(fecha, hora, servicio, chat_id, email)
        datos["google_event_id"] = google_id 

        # Obtener ubicación (Sesión rápida)
        ubi = "Calle 65a No. 264, Mérida."
        db = SessionLocal()
        try:
            config = db.query(ConfiguracionBot).first()
            if config and config.ubicacion_contacto: ubi = config.ubicacion_contacto
        finally: db.close()

        await enviar_correo_confirmacion(email, fecha, hora, servicio, ubi)
        res_ok = f"✅ **¡Cita agendada con éxito!**\n\nAsesoría: {servicio}\nFecha: {fecha} {hora}\n\n¡Te esperamos!"
        return limpiar_emojis(res_ok), "guardar_cita_db", datos, "NORMAL"

    elif detectar_intencion_ubicacion(texto_usuario):
        return "📍 Calle 65a No. 264, Residencial Floresta. ¡Te esperamos!", "enviar_mapa", None, estado_actual

    elif detectar_despedida(texto_usuario):
        return openai_cache.MENSAJE_DESPEDIDA_CACHED, None, None, estado_actual

    elif detectar_saludo(texto_usuario):
        return openai_cache.MENSAJE_SALUDO_CACHED, None, None, estado_actual

    else:
        # --- LLAMADA EXTERNA (DB LIBRE) ---
        res_ia = await obtener_respuesta_ia_optimizada(historial)

        # Limpieza absoluta de etiquetas de control en cualquier formato
        res_limpia = res_ia.replace("[ACTIVAR_AGENDA]", "").replace("ACTIVAR_AGENDA", "").strip()

        if "ACTIVAR_AGENDA" in res_ia:
            print("🔄 [ORQUESTADOR] Transición detectada vía etiqueta.")
            return limpiar_emojis(res_limpia), None, None, "AGENDANDO"

        return limpiar_emojis(res_limpia), None, None, estado_actual