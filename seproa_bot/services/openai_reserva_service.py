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


async def obtener_extraccion_ia(historial_mensajes: list, horarios_texto: str, nombres_servicios: list) -> dict:
    zona_horaria = pytz.timezone('America/Merida')
    ahora = datetime.now(zona_horaria)
    fecha_actual = ahora.strftime('%Y-%m-%d')
    hora_actual = ahora.strftime('%H:%M')

    print(f"⏰ [Extracción IA] Contexto temporal para la IA: Fecha actual: {fecha_actual}, Hora actual: {hora_actual}, servicios {', '.join(nombres_servicios)}")
    
    # Herramienta para la extracción de intenciones y datos de agendamiento usando OpenAI Function Calling
    HERRAMIENTA_EXTRACCION = [
        {
            "type": "function",
            "function": {
                "name": "extraer_datos_cita",
                "description": "Extrae datos de agendamiento y controla el estado de confirmación.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "intencion": {
                            "type": "string",
                            "enum": ["solo_informacion", "quiere_agendar"]
                        },
                        "servicio_detectado": {
                            "type": "string",
                            "enum": nombres_servicios,
                            "description": "Clasifica el servicio, separándolos estrictamente entre ellos. Opciones válidas: {', '.join(nombres_servicios)}. Si el usuario no sabe o es otra cosa, usa 'General'."
                        },
                        "fecha": { "type": "string" },
                        "hora": { "type": "string" },
                        "email": {
                            "type": "string",
                            "description": "Correo electrónico del usuario. Devuelve null si aún no lo ha escrito."
                        },
                        "confirmacion_final": {
                            "type": "boolean",
                            "description": "True SOLAMENTE si el bot ya mostró el resumen completo (servicio, fecha, hora, email) y el usuario acaba de responder explícitamente 'Sí' o 'Confirmar'. En cualquier otro caso, False."
                        }
                    },
                    "required": ["intencion", "servicio_detectado"]
                }
            }
        }
    ]

    prompt_extraccion = f"""Eres el motor de validación de SEPROA. Extrae datos usando la herramienta con estas REGLAS ESTRICTAS E INQUEBRANTABLES:

1. CONTEXTO TEMPORAL ACTUAL: Hoy es {fecha_actual} y son las {hora_actual} en Mérida. No agendes en el pasado.
2. REGLA DEL PASADO: Está ESTRICTAMENTE PROHIBIDO extraer fechas u horas que ya pasaron. Si el usuario pide algo en el pasado, la fecha y hora deben ser 'null'.
3. REGLA DE MARGEN (2 HORAS): No se pueden agendar citas urgentes. La hora extraída debe tener al menos 2 horas de diferencia con la hora actual.
4. REGLA DE HORAS EN PUNTO: Las citas duran 1 hora exacta. Solo puedes extraer horas completas (ej. 09:00, 12:00, 15:00). NUNCA extraigas minutos fraccionados (ej. 10:30, 15:15). Si el usuario pide fracciones, la hora debe ser 'null'.
5. CIERRE DE SUCURSAL: Las citas duran 1 hora. La ÚLTIMA cita permitida es UNA HORA ANTES de la hora de cierre. (Ej. Si en el horario dice que cierran a las 15:00, la última hora en la que puedes agendar es a las 14:00). Si pide a la hora de cierre para la cita, devuelve null en la hora.
6. CORREO Y CONFIRMACIÓN: Extrae el email si el usuario lo menciona en cualquier formato (ej. correo@gmail.com, "mi correo es...", etc.). La 'confirmacion_final' solo debe ser True si el usuario acepta explícitamente ("sí", "confirmo") después de haberle mostrado el resumen completo.
7. REGLA DE DISPONIBILIDAD: Estos son nuestros horarios comerciales:
{horarios_texto} Para agendar una cita la hora debe ser menor al horario de cierre, donde la última hora disponible es exactamente UNA HORA ANTES del cierre.
Solo extrae horas que caigan dentro de estos bloques. Si pide fuera de horario o justo a la hora de cierre, la hora debe ser 'null'.
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