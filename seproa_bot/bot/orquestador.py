# bot/orquestador.py
from bot.detectores import (
    detectar_ataque_inyeccion,
    detectar_intencion_transaccional,
    detectar_intencion_ubicacion,
    detectar_saludo,
    detectar_despedida
)
from services.openai_service import obtener_respuesta_ia_optimizada
import services.openai_service as openai_cache # Para acceder a las variables globales

async def procesar_intencion(texto_usuario: str, historial: list, es_nuevo_usuario: bool) -> tuple[str, str]:
    """
    Evalúa la intención del usuario y decide qué motor usar.
    Retorna: (texto_de_respuesta, accion_especial)
    """
    if detectar_ataque_inyeccion(texto_usuario):
        print("🚨 [Seguridad] Intento de Prompt Injection detectado y bloqueado.")
        # Respuesta estéril corporativa
        respuesta_segura = "Lo siento, por políticas de seguridad de SEPROA no puedo procesar esa solicitud ni revelar información interna del sistema. ¿En qué más te puedo ayudar respecto a nuestros servicios?"
        return respuesta_segura, None

    if es_nuevo_usuario:
        print("👋 [Ruta] Nuevo Usuario - Saludo Caché")
        return openai_cache.MENSAJE_SALUDO_CACHED, None

    if detectar_intencion_transaccional(texto_usuario):
        print("🔍 [Ruta] Transaccional / Agendamiento")
        respuesta = "Veo que te interesa un servicio o agendar una cita. (Próximamente OpenAI Function Calling)"
        return respuesta, "extraer_datos"

    elif detectar_intencion_ubicacion(texto_usuario):
        print("🗺️ [Ruta] Ubicación")
        respuesta = "📍 Nos encontramos ubicados en la Calle 65a No. 264, Residencial Floresta. ¡Te esperamos!"
        return respuesta, "enviar_mapa"

    elif detectar_despedida(texto_usuario):
        print("👋 [Ruta] Despedida Caché")
        return openai_cache.MENSAJE_DESPEDIDA_CACHED, None

    elif detectar_saludo(texto_usuario):
        print("🤝 [Ruta] Saludo Caché")
        return openai_cache.MENSAJE_SALUDO_CACHED, None

    else:
        print("🧠 [Ruta] Consulta General -> LLM OpenAI")
        respuesta_llm = await obtener_respuesta_ia_optimizada(historial)
        return respuesta_llm, None