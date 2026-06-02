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
from datetime import datetime
from services.google_calendar_service import verificar_disponibilidad, agendar_cita_google
from services.email_service import enviar_correo_confirmacion

async def procesar_intencion(texto_usuario: str, historial: list, es_nuevo_usuario: bool, chat_id: str, estado_actual: str) -> tuple[str, str, dict, str]:
    """
    Evalúa la intención del usuario y decide qué motor usar.
    Retorna: (texto_de_respuesta, accion_especial)
    """
    texto_limpio = texto_usuario.lower()
    
    # 0. DETECCIÓN DE ATAQUES DE INYECCIÓN (Prompt Injection)
    if detectar_ataque_inyeccion(texto_usuario):
        print("🚨 [Seguridad] Intento de Prompt Injection detectado y bloqueado.")
        # Respuesta estéril corporativa
        respuesta_segura = "Lo siento, por políticas de seguridad de SEPROA no puedo procesar esa solicitud ni revelar información interna del sistema. ¿En qué más te puedo ayudar respecto a nuestros servicios?"
        return respuesta_segura, None, None, estado_actual

    # 0.5 Comando de escape para abortar procesos ("cancelar agendar")
    if estado_actual == "AGENDANDO" and "cancelar agendar" in texto_limpio:
        print("🛑 [Estado] El usuario usó el comando de escape para abortar.")
        return "Has cancelado el proceso de agendamiento. 🛑\n¿En qué más te puedo ayudar el día de hoy?", None, None, "NORMAL"

    if es_nuevo_usuario:
        print("👋 [Ruta] Nuevo Usuario - Saludo Caché")
        return openai_cache.MENSAJE_SALUDO_CACHED, None, None, "NORMAL"

    # =========================================================================
    # 1. MÁQUINA DE ESTADOS:
    # Entra aquí si la BD dice "AGENDANDO" *O* si usó una palabra clave inicial
    # =========================================================================
    if estado_actual == "AGENDANDO" or detectar_intencion_transaccional(texto_usuario):
        print(f"🔍 [Modo Cita] Estado actual BD: {estado_actual}")

        horarios_disponibles = 'Lunes a Viernes de 9:00 a 15:00'
        # 1. Sacamos el JSON de la IA
        datos = await obtener_extraccion_ia(historial, horarios_disponibles)

        intencion = datos.get("intencion")
        servicio = datos.get("servicio_detectado", "General")
        fecha = datos.get("fecha")
        email = datos.get("email")
        hora = datos.get("hora")
        confirmado = datos.get("confirmacion_final", False)

        # 2. Si solo preguntaba información, se lo devolvemos al cerebro normal
        if intencion == "solo_informacion" and estado_actual != "AGENDANDO":
            respuesta_llm = await obtener_respuesta_ia_optimizada(historial)
            return respuesta_llm, "actualizar_clasificacion", datos, "NORMAL"

        nuevo_estado = "AGENDANDO"

        # Validaciones estrictas de formato y lógica para la fecha y hora
        fecha_invalida = not fecha or str(fecha).strip().lower() in ["null", "none", ""]
        hora_invalida = not hora or str(hora).strip().lower() in ["null", "none", ""]


        # Validación 2: Fines de semana
        if not fecha_invalida:
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
                if fecha_obj.weekday() >= 5: 
                    fecha_invalida = True 
            except ValueError:
                fecha_invalida = True

        # Validación 3: Límite de las 15:00 hrs
        if not hora_invalida:
            try:
                hora_int = int(str(hora).split(":")[0])
                if hora_int >= 15: 
                    hora_invalida = True
            except Exception:
                hora_invalida = True

        # 3. Quiere agendar, pero le FALTAN datos
        if fecha_invalida or hora_invalida:
            respuesta_faltante = (
                f"Para agendar tu cita de {servicio}, necesito una fecha y hora exactas. 📅\n\n"
                f"Recuerda nuestras reglas de agenda:\n"
                f"• Citas de hora en punto (ej. 10:00, 16:00)\n"
                f"• Al menos 2 horas de anticipación\n"
                f"• No agendamos fines de semana\n"
                f"• Horarios comerciales: {horarios_disponibles}\n\n"
                f"¿Qué día y hora prefieres?"
                f"*(Si deseas salir de este proceso en cualquier momento, escribe **CANCELAR AGENDAR**)*."
            )
            return respuesta_faltante, "actualizar_clasificacion", datos, nuevo_estado
        
        # 4. Revisar disponibilidad en Google Calendar antes de confirmar la cita
        print(f"📅 Consultando API de Google Calendar para {fecha} {hora}...")
        esta_disponible = await verificar_disponibilidad(fecha, hora)
        
        if not esta_disponible:
            print("⚠️ Choque de horario en Google Calendar.")
            respuesta_choque = f"Lo lamento mucho, pero ya está de reservado el espacio del {fecha} a las {hora}. 📅\n\n¿Te gustaría intentar con otra hora u otro día?"
            return respuesta_choque, "actualizar_clasificacion", datos, nuevo_estado

        # 5. Pedir  antes de agendar
        if not email:
            respuesta_correo = f"¡Excelente! Tenemos espacio el {fecha} a las {hora}. 📧 Para enviarte la invitación a tu calendario, ¿cuál es tu correo electrónico?"
            return respuesta_correo, "actualizar_clasificacion", datos, nuevo_estado

        # 6. Confirmar la cita
        if not confirmado:
            respuesta_confirmacion = (
                f"📋 **RESUMEN DE TU CITA**\n\n"
                f"🔹 **Servicio:** {servicio}\n"
                f"📅 **Fecha:** {fecha}\n"
                f"⏰ **Hora:** {hora}\n"
                f"📧 **Correo:** {email}\n\n"
                f"¿Todos los datos son correctos? Responde *'Sí'* para confirmar y agendar formalmente."
            )
            return respuesta_confirmacion, "actualizar_clasificacion", datos, nuevo_estado

        # Si hay espacio, lo agendamos directamente desde aquí
        print("✅ Horario libre. Creando evento en Google...")
        google_event_id = await agendar_cita_google(fecha, hora, servicio, chat_id, email)
        datos["google_event_id"] = google_event_id 

        print("📧 Enviando correo al cliente...")
        await enviar_correo_confirmacion(email, fecha, hora, servicio)

        respuesta_exito = (
            f"✅ **¡Tu cita ha sido agendada con éxito en nuestro calendario corporativo!**\n\n"
            f"**Servicio:** Asesoría {servicio}\n"
            f"**Fecha:** {fecha}\n"
            f"**Hora:** {hora}\n\n"
            f"Te enviaremos un recordatorio 24 horas antes. ¡Te esperamos en SEPROA!"
        )
        
        # Le decimos al webhook que todo salió bien y que guarde en BD
        return respuesta_exito, "guardar_cita_db", datos, "NORMAL"

    elif detectar_intencion_ubicacion(texto_usuario):
        print("🗺️ [Ruta] Ubicación")
        respuesta = "📍 Nos encontramos ubicados en la Calle 65a No. 264, Residencial Floresta. ¡Te esperamos!"
        return respuesta, "enviar_mapa", None, estado_actual

    elif detectar_despedida(texto_usuario):
        print("👋 [Ruta] Despedida Caché")
        return openai_cache.MENSAJE_DESPEDIDA_CACHED, None, None, estado_actual

    elif detectar_saludo(texto_usuario):
        print("🤝 [Ruta] Saludo Caché")
        return openai_cache.MENSAJE_SALUDO_CACHED, None, None, estado_actual

    else:
        print("🧠 [Ruta] Consulta General -> LLM OpenAI")
        respuesta_llm = await obtener_respuesta_ia_optimizada(historial)
        return respuesta_llm, None, None, estado_actual