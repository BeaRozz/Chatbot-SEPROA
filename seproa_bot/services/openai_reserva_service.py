import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json
from datetime import datetime
import pytz

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente asíncrono de OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Herramienta para la extracción de intenciones y datos de agendamiento usando OpenAI Function Calling
HERRAMIENTA_EXTRACCION = [
    {
        "type": "function",
        "function": {
            "name": "extraer_datos_cita",
            "description": "Extrae datos de agendamiento siguiendo reglas de negocio estrictas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intencion": {
                        "type": "string",
                        "enum": ["solo_informacion", "quiere_agendar"],
                        "description": "Si solo pregunta detalles es 'solo_informacion'. Si pide explícitamente una cita, es 'quiere_agendar'."
                    },
                    "servicio_detectado": {
                        "type": "string",
                        "enum": ["Fiscal", "Contable", "Administrativa", "General"]
                    },
                    "fecha": {
                        "type": "string",
                        "description": "Fecha en YYYY-MM-DD. Si no la menciona explícitamente o pide algo ilegal, devuelve null."
                    },
                    "hora": {
                        "type": "string",
                        "description": "Hora en formato HH:00 (Ej. 09:00, 14:00). SIEMPRE en punto. Si pide fracciones (Ej. 10:30), devuélvela redondeada a la hora más cercana o null si es inválida."
                    }
                },
                "required": ["intencion", "servicio_detectado"]
            }
        }
    }
]

async def obtener_extraccion_ia(historial_mensajes: list, horarios_texto: str) -> dict:
    zona_horaria = pytz.timezone('America/Merida')
    ahora = datetime.now(zona_horaria)
    fecha_actual = ahora.strftime('%Y-%m-%d')
    hora_actual = ahora.strftime('%H:%M')
    
    prompt_extraccion = f"""Eres el motor de validación de SEPROA. Extrae datos usando la herramienta con estas REGLAS ESTRICTAS E INQUEBRANTABLES:

1. CONTEXTO TEMPORAL ACTUAL: Hoy es {fecha_actual} y son las {hora_actual} en Mérida.
2. REGLA DEL PASADO: Está ESTRICTAMENTE PROHIBIDO extraer fechas u horas que ya pasaron. Si el usuario pide algo en el pasado, la fecha y hora deben ser 'null'.
3. REGLA DE MARGEN (2 HORAS): No se pueden agendar citas urgentes. La hora extraída debe tener al menos 2 horas de diferencia con la hora actual.
4. REGLA DE HORAS EN PUNTO: Las citas duran 1 hora exacta. Solo puedes extraer horas completas (ej. 09:00, 12:00, 15:00). NUNCA extraigas minutos fraccionados (ej. 10:30, 15:15). Si el usuario pide fracciones, la hora debe ser 'null'.
5. REGLA DE DISPONIBILIDAD: Estos son nuestros horarios comerciales:
{horarios_texto}
Solo extrae horas que caigan dentro de estos bloques. Si pide fuera de horario, la hora debe ser 'null'.
"""

    mensajes_api = [{"role": "system", "content": prompt_extraccion}] + historial_mensajes

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensajes_api,
            tools=HERRAMIENTA_EXTRACCION,
            tool_choice={"type": "function", "function": {"name": "extraer_datos_cita"}},
            temperature=0.0 # Reducimos la temperatura a 0 para máxima precisión matemática
        )
        argumentos = response.choices[0].message.tool_calls[0].function.arguments
        return json.loads(argumentos)
    except Exception as e:
        print(f"❌ Error en Extracción: {e}")
        return {"intencion": "solo_informacion", "servicio_detectado": "General", "fecha": None, "hora": None}