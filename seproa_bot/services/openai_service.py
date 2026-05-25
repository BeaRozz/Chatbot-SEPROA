import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente asíncrono de OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Definición robusta del System Prompt
PROMPT_NORMAL = """Eres el Asistente Virtual Automatizado de SEPROA.
Catálogo de servicios:
{servicios}

Horarios de atención estandarizados:
{horarios_atencion}

Base de Conocimientos (FAQs):
{preguntas_frecuentes}

Reglas de interacción:
1. Actúa bajo el tono de comunicación '{tono_etiqueta}': {tono_descripcion}
2. Emojis: {instruccion_emojis}
3. Mantén tus respuestas muy breves (máximo 50 palabras).
4. No inventes información.
"""

PROMPT_VACACIONES = """Eres el Asistente Virtual de SEPROA. 
¡REGLA DE ORO! Actualmente la empresa ESTÁ DE VACACIONES y no labora. Regresarán el {fecha_regreso}.
Tu ÚNICA tarea es informar amablemente al usuario que la empresa está cerrada por vacaciones y cuándo regresan. 
Bajo NINGUNA circunstancia respondas dudas sobre servicios, precios o agendas. Solo discúlpate e informa del cierre.
"""

async def obtener_respuesta_ia(
    historial_mensajes: list, config, tono_etiqueta: str, tono_descripcion: str, 
    texto_servicios: str, texto_faqs: str, texto_horarios: str
) -> str:
    
    # Evaluar la regla estricta de vacaciones
    if config.modo_vacaciones:
        system_prompt_dinamico = PROMPT_VACACIONES.format(fecha_regreso=config.fecha_regreso)
    else:
        instruccion_emojis = "Úsalos naturalmente" if config.usa_emojis else "PROHIBIDO usar emojis."
        system_prompt_dinamico = PROMPT_NORMAL.format(
            tono_etiqueta=tono_etiqueta,
            tono_descripcion=tono_descripcion,
            instruccion_emojis=instruccion_emojis,
            servicios=texto_servicios,
            horarios_atencion=texto_horarios,
            preguntas_frecuentes=texto_faqs
        )

    mensajes_api = [{"role": "system", "content": system_prompt_dinamico}] + historial_mensajes

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensajes_api,
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error OpenAI: {e}")
        return "Disculpa, tengo dificultades técnicas. Intenta en un momento."