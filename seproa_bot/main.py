import os
from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
import httpx
from dotenv import load_dotenv

# Importaciones locales
from db import models
from db.database import engine, get_db

# 1. Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener el token de forma segura
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("¡Falta el TELEGRAM_BOT_TOKEN en el archivo .env!")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# 2. Crear las tablas en la base de datos SQLite si no existen
models.Base.metadata.create_all(bind=engine)

# 3. Inicializar la aplicación FastAPI
app = FastAPI(title="SEPROA Chatbot Empresarial")

@app.get("/")
async def root():
    """Endpoint de comprobación de salud del servidor."""
    return {"mensaje": "Servidor de SEPROA Bot corriendo exitosamente"}

@app.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint asíncrono que recibe las actualizaciones de Telegram.
    """
    update = await request.json()
    
    # Verificar si la actualización contiene un mensaje de texto
    if "message" in update and "text" in update["message"]:
        chat_id = str(update["message"]["chat"]["id"])
        texto_usuario = update["message"]["text"]
        
        # --- LÓGICA DE BASE DE DATOS ---
        
        # A. Registrar usuario si es la primera vez
        usuario = db.query(models.Usuario).filter(models.Usuario.telegram_id == chat_id).first()
        if not usuario:
            nuevo_usuario = models.Usuario(telegram_id=chat_id)
            db.add(nuevo_usuario)
            db.commit()
            
        # B. Guardar el mensaje del usuario en el historial
        msg_usuario = models.Mensaje(telegram_id=chat_id, rol="usuario", contenido=texto_usuario)
        db.add(msg_usuario)
        
        # C. Preparar la respuesta "Eco" y guardarla en el historial
        texto_respuesta = f"Eco de SEPROA Bot: {texto_usuario}"
        msg_bot = models.Mensaje(telegram_id=chat_id, rol="bot", contenido=texto_respuesta)
        db.add(msg_bot)
        
        # Confirmar los cambios en la base de datos
        db.commit()
        
        # --- COMUNICACIÓN CON TELEGRAM ---
        
        # D. Enviar la respuesta a Telegram de forma asíncrona
        payload = {
            "chat_id": chat_id,
            "text": texto_respuesta
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
            
    # Siempre debemos responder a Telegram con un status 200 (ok)
    # para que no intente reenviar el mensaje
    return {"status": "ok"}