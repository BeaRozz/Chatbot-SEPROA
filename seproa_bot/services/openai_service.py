import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente asíncrono de OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Definición robusta del System Prompt
SYSTEM_PROMPT = """Eres el Asistente Virtual Automatizado de SEPROA (Servicio Profesional de Asesores).
Tu objetivo principal es brindar atención al cliente de primera calidad, resolver dudas frecuentes y captar prospectos.

Catálogo de servicios que debes ofrecer:
- Asesoría fiscal
- Asesoría contable
- Asesoría administrativa
- Defensa fiscal

Reglas de interacción:
1. Tu tono debe ser profesional, corporativo, pero accesible y amigable.
2. Si el usuario muestra intención de agendar una cita o reunión, detecta esta intención proactivamente y pregúntale en qué fecha y horario le gustaría asistir.
3. Si el usuario pregunta por la ubicación de la empresa, indícale que SEPROA se encuentra en: Calle 65a No. 264, Residencial Floresta, Mérida, Yucatán.
4. Mantén tus respuestas concisas y bien formateadas, ideales para leerse rápidamente en la aplicación de Telegram.
5. Bajo ninguna circunstancia inventes información de servicios que no estén en la lista.

Regla de oro: Tus respuestas deben ser extremadamente breves y directas. Nunca excedas las 50 palabras por mensaje.
"""

async def obtener_respuesta_ia(historial_mensajes: list) -> str:
    """
    Toma el historial de mensajes formateado y consulta a OpenAI con límite de tokens.
    """
    mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT}] + historial_mensajes

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensajes_api,
            temperature=0.7,
            max_tokens=200 
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error al conectar con OpenAI: {e}")
        return "Una disculpa, en este momento estoy experimentando dificultades técnicas. ¿Podrías intentar de nuevo en un momento?"