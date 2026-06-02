import os
import datetime
import pytz
import asyncio
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
ZONA_HORARIA = pytz.timezone('America/Merida')

def obtener_servicio_calendario():
    """Autentica y devuelve el cliente de la API de Google Calendar."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

def _verificar_disponibilidad_sync(fecha_str: str, hora_str: str) -> bool:
    """Función síncrona interna para checar si hay eventos en ese horario."""
    servicio = obtener_servicio_calendario()
    
    # Armamos la fecha de inicio y fin (asumimos citas de 1 hora)
    inicio_str = f"{fecha_str} {hora_str}"
    inicio_dt = ZONA_HORARIA.localize(datetime.datetime.strptime(inicio_str, "%Y-%m-%d %H:%M"))
    fin_dt = inicio_dt + datetime.timedelta(hours=1)
    
    # Convertimos a formato RFC3339 requerido por Google
    inicio_rfc = inicio_dt.isoformat()
    fin_rfc = fin_dt.isoformat()
    
    # Consultamos si hay eventos que se empalmen
    eventos_result = servicio.events().list(
        calendarId=CALENDAR_ID,
        timeMin=inicio_rfc,
        timeMax=fin_rfc,
        singleEvents=True
    ).execute()
    
    eventos = eventos_result.get('items', [])
    return len(eventos) == 0 # Devuelve True si está disponible (0 eventos)

def _crear_evento_sync(fecha_str: str, hora_str: str, tipo_servicio: str, telegram_id: str, email_cliente: str) -> str:
    servicio = obtener_servicio_calendario()
    
    inicio_str = f"{fecha_str} {hora_str}"
    inicio_dt = ZONA_HORARIA.localize(datetime.datetime.strptime(inicio_str, "%Y-%m-%d %H:%M"))
    fin_dt = inicio_dt + datetime.timedelta(hours=1)
    
    evento = {
        'summary': f'Asesoría {tipo_servicio} - Prospecto',
        # Agregamos el email a la descripción para que SEPROA lo tenga a la mano
        'description': f'Cita generada por Telegram.\nID: {telegram_id}\nCorreo del cliente: {email_cliente}',
        'start': { 'dateTime': inicio_dt.isoformat(), 'timeZone': 'America/Merida' },
        'end': { 'dateTime': fin_dt.isoformat(), 'timeZone': 'America/Merida' },
        'colorId': '5'
        # ❌ ELIMINAMOS 'attendees' y 'reminders' para que Google no nos bloquee
    }

    evento_creado = servicio.events().insert(
        calendarId=CALENDAR_ID, 
        body=evento
    ).execute()
    
    return evento_creado.get('id')

async def agendar_cita_google(fecha_str: str, hora_str: str, tipo_servicio: str, telegram_id: str, email_cliente: str) -> str:
    # Actualizamos el wrapper asíncrono
    return await asyncio.to_thread(_crear_evento_sync, fecha_str, hora_str, tipo_servicio, telegram_id, email_cliente)

# -------------------------------------------------------------------
# WRAPPERS ASÍNCRONOS (Para no bloquear FastAPI)
# -------------------------------------------------------------------
async def verificar_disponibilidad(fecha_str: str, hora_str: str) -> bool:
    return await asyncio.to_thread(_verificar_disponibilidad_sync, fecha_str, hora_str)