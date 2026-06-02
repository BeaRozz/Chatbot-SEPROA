# bot/detectores.py
import re

def detectar_intencion_ubicacion(texto: str) -> bool:
    keywords = [
        "ubicación", "ubicacion", "dónde están", "donde estan", "dónde son", "ubican",
        "dirección", "direccion", "cómo llegar", "como llegar", "los encuentro",
        "encuentran", "mapa", "oficina", "sucursal", "dónde se ubican", "encontrarlos", "localización", "localizacion"
    ]
    return any(k in texto.lower() for k in keywords)

def detectar_intencion_transaccional(texto_usuario: str, ultimo_mensaje_bot: str = "") -> bool:
    texto_limpio = texto_usuario.lower()
    keywords = [
        "reservar", "reserva", "reservacion", "reservación", 
        "cita", "agendar", "agenda", "apartar", "turno", "contratar",
        "asesoría", "fiscal", "contable", "administrativa", "cotización", "precio", "costo"
    ]
    
    if any(k in texto_limpio for k in keywords):
        return True

    if ultimo_mensaje_bot:
        contexto_citas = ["agendar", "cita", "asesoría"]
        respuestas_afirmativas = ["si", "sí", "claro", "por favor", "ok", "me parece bien", "va", "perfecto", "bueno"]
        
        # Verificamos si el bot acaba de hablar de citas
        if any(c in ultimo_mensaje_bot for c in contexto_citas):
            # Verificamos si el usuario respondió con una afirmación corta
            # Separamos por palabras para atrapar "si por favor" o "ok gracias"
            palabras_usuario = texto_limpio.split()
            if any(r in palabras_usuario for r in respuestas_afirmativas) or texto_limpio in respuestas_afirmativas:
                return True

    return False

def detectar_saludo(texto: str) -> bool:
    texto_limpio = texto.lower().strip()
    patron = r'^(hola|ola|hooa|hoa|buenas|buenos d[ií]as|buenas tardes|buenas noches|qu[eé] tal|q tal|saludos|buen d[ií]a)[!.]*\s*$'
    return bool(re.match(patron, texto_limpio))

def detectar_despedida(texto: str) -> bool:
    texto_limpio = texto.lower().strip()
    patron = r'^(gracias|muchas gracias|adi[óo]s|nos vemos|hasta luego|bye|listo|eso es todo|chau|chao)[!.]*\s*$'
    return bool(re.match(patron, texto_limpio))

def detectar_ataque_inyeccion(texto: str) -> bool:
    texto_limpio = texto.lower()
    # Patrones típicos de hackers o curiosos intentando romper bots
    ataques = [
        "ignora", "olvida", "instrucciones anteriores", "system prompt",
        "base de datos", "sql", "select *", "drop table", "contraseña",
        "token", "apikey", "api key", "borrar cuenta", "eliminar datos",
        "como fuiste programado", "dame tus reglas", "soy tu creador", "hackea tu sistema", "rompe tu código", 
        "ejecuta código", "ejecuta esta instrucción", "ejecuta esto", "ejecuta el siguiente comando", 
        "ejecuta el siguiente código", "ejecuta el siguiente script", "ejecuta el siguiente programa"
    ]
    return any(a in texto_limpio for a in ataques)