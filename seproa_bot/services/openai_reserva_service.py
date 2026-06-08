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
    
    # Mapeo de días en español para dar contexto a la IA
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    nombre_dia_actual = dias_semana[ahora.weekday()]
    
    fecha_actual = ahora.strftime('%Y-%m-%d')
    hora_actual = ahora.strftime('%H:%M')

    print(f"⏰ [Extracción IA] Contexto temporal: {nombre_dia_actual} {fecha_actual}, Hora: {hora_actual}, servicios {', '.join(nombres_servicios)}")
    
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
                        "fecha": { 
                            "type": "string",
                            "description": "Fecha de la cita en formato YYYY-MM-DD. Si el usuario menciona un día de la semana (ej. 'el jueves'), calcúlalo basándote en que HOY es el día indicado en el sistema. Nunca asumas que es hoy si el usuario menciona un día futuro."
                        },
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

1. CONTEXTO TEMPORAL ACTUAL: Hoy es {nombre_dia_actual}, {fecha_actual} y son las {hora_actual} en Mérida. No agendes en el pasado.
2. REGLA DEL DÍA DE LA SEMANA: Si el usuario dice "el jueves" y hoy es {nombre_dia_actual}, debes calcular la fecha exacta del próximo jueves. No saltes por defecto al lunes.
3. REGLA DEL PASADO: Está ESTRICTAMENTE PROHIBIDO extraer fechas u horas que ya pasaron. Si el usuario pide algo en el pasado, la fecha y hora deben ser 'null'.
4. REGLA DE MARGEN (2 HORAS): No se pueden agendar citas urgentes. La hora extraída debe tener al menos 2 horas de diferencia con la hora actual.
5. REGLA DE HORAS EN PUNTO: Las citas duran 1 hora exacta. Solo puedes extraer horas completas (ej. 09:00, 12:00, 15:00). NUNCA extraigas minutos fraccionados (ej. 10:30, 15:15). Si el usuario pide fracciones, la hora debe ser 'null'.
6. CIERRE DE SUCURSAL: Las citas duran 1 hora. La ÚLTIMA cita permitida es UNA HORA ANTES de la hora de cierre. (Ej. Si en el horario dice que cierran a las 15:00, la última hora en la que puedes agendar es a las 14:00). Si pide a la hora de cierre para la cita, devuelve null en la hora.
7. CORREO Y CONFIRMACIÓN: Extrae el email si el usuario lo menciona en cualquier formato (ej. correo@gmail.com, "mi correo es...", etc.). La 'confirmacion_final' solo debe ser True si el usuario acepta explícitamente ("sí", "confirmo") después de haberle mostrado el resumen completo.
8. REGLA DE DISPONIBILIDAD: Estos son nuestros horarios comerciales:
{horarios_texto} Para agendar una cita la hora debe ser menor al horario de cierre, donde la última hora disponible es exactamente UNA HORA ANTES del cierre.
9. ACTUALIZACIÓN DINÁMICA (CORRECCIONES): Siempre debes darle prioridad absoluta al ÚLTIMO mensaje del usuario. Si el usuario cambia de opinión, se corrige o propone un nuevo día/hora (ej. "no, mejor el martes"), DEBES actualizar tu extracción con el nuevo dato y descartar el anterior.
Solo extrae horas que caigan dentro de estos bloques. Si pide fuera de horario o justo a la hora de cierre, la hora debe ser 'null'.
"""

    mensajes_api = [{"role": "system", "content": prompt_extraccion}] + historial_mensajes

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensajes_api,
            tools=HERRAMIENTA_EXTRACCION,
            tool_choice={"type": "function", "function": {"name": "extraer_datos_cita"}},
            temperature=0.0, # Reducimos la temperatura a 0 para máxima precisión matemática
            timeout=25.0
        )
        argumentos = response.choices[0].message.tool_calls[0].function.arguments
        return json.loads(argumentos)
    except Exception as e:
        print(f"❌ Error en Extracción: {e}")
        return {"intencion": "solo_informacion", "servicio_detectado": "General", "fecha": None, "hora": None}