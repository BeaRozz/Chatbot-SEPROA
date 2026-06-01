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

async def procesar_intencion(texto_usuario: str, historial: list, es_nuevo_usuario: bool) -> tuple[str, str]:
    """
    Evalúa la intención del usuario y decide qué motor usar.
    Retorna: (texto_de_respuesta, accion_especial)
    """
    if detectar_ataque_inyeccion(texto_usuario):
        print("🚨 [Seguridad] Intento de Prompt Injection detectado y bloqueado.")
        # Respuesta estéril corporativa
        respuesta_segura = "Lo siento, por políticas de seguridad de SEPROA no puedo procesar esa solicitud ni revelar información interna del sistema. ¿En qué más te puedo ayudar respecto a nuestros servicios?"
        return respuesta_segura, None, None

    if es_nuevo_usuario:
        print("👋 [Ruta] Nuevo Usuario - Saludo Caché")
        return openai_cache.MENSAJE_SALUDO_CACHED, None, None

    ultimo_mensaje_bot = ""
    if historial:
        # Buscamos el último mensaje donde el rol haya sido "assistant"
        for msg in reversed(historial):
            if msg["role"] == "assistant":
                ultimo_mensaje_bot = msg["content"]
                break

    if detectar_intencion_transaccional(texto_usuario, ultimo_mensaje_bot):
        print("🔍 [Ruta] Transaccional / Agendamiento")

        horarios_disponibles = getattr(openai_cache, 'horarios_atencion', 'Lunes a Viernes de 9:00 a 15:00')
        # 1. Sacamos el JSON de la IA
        datos = await obtener_extraccion_ia(historial, horarios_disponibles)
        intencion = datos.get("intencion")
        servicio = datos.get("servicio_detectado", "General")
        fecha = datos.get("fecha")
        hora = datos.get("hora")

        # 2. Si solo preguntaba información, se lo devolvemos al cerebro normal
        if intencion == "solo_informacion":
            respuesta_llm = await obtener_respuesta_ia_optimizada(historial)
            return respuesta_llm, "actualizar_clasificacion", datos

        fecha_invalida = not fecha or str(fecha).strip().lower() in ["null", "none", ""]
        hora_invalida = not hora or str(hora).strip().lower() in ["null", "none", ""]

        # Validación Matemática del Calendario
        if not fecha_invalida:
            try:
                # Convertimos el string "2026-06-28" a un objeto calendario real de Python
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
                # weekday() devuelve 5 para Sábado y 6 para Domingo
                if fecha_obj.weekday() >= 5: 
                    fecha_invalida = True # Forzamos el fallo
            except ValueError:
                # Por si la IA manda un formato loco que no sea YYYY-MM-DD
                fecha_invalida = True

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
            )
            return respuesta_faltante, "actualizar_clasificacion", datos
        
        # 4. TENEMOS TODO LISTO PARA GOOGLE CALENDAR
        respuesta_exito = f"¡Perfecto! Revisaré mi sistema para agendar tu asesoría {servicio} el día {fecha} exactamente a las {hora}. Permíteme un segundo... ⏳"
        return respuesta_exito, "agendar_calendario", datos

    elif detectar_intencion_ubicacion(texto_usuario):
        print("🗺️ [Ruta] Ubicación")
        respuesta = "📍 Nos encontramos ubicados en la Calle 65a No. 264, Residencial Floresta. ¡Te esperamos!"
        return respuesta, "enviar_mapa", None

    elif detectar_despedida(texto_usuario):
        print("👋 [Ruta] Despedida Caché")
        return openai_cache.MENSAJE_DESPEDIDA_CACHED, None, None

    elif detectar_saludo(texto_usuario):
        print("🤝 [Ruta] Saludo Caché")
        return openai_cache.MENSAJE_SALUDO_CACHED, None, None

    else:
        print("🧠 [Ruta] Consulta General -> LLM OpenAI")
        respuesta_llm = await obtener_respuesta_ia_optimizada(historial)
        return respuesta_llm, None, None