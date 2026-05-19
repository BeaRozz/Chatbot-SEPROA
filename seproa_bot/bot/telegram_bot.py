import os
import httpx
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from db.database import get_db
from db.models import Usuario, Mensaje
from services.openai_service import obtener_respuesta_ia

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    if "message" not in data:
        return {"status": "ok"}
        
    chat_id_int = data["message"]["chat"]["id"]
    chat_id = str(chat_id_int) 
    texto_usuario = data["message"].get("text", "")
    
    if not texto_usuario:
        return {"status": "ok"}

    # 1. Gestión de Usuario
    usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
    if not usuario:
        usuario = Usuario(telegram_id=chat_id)
        db.add(usuario)
        db.commit()

    # 2. Guardar el nuevo mensaje del usuario
    # Ajustado a los nombres: telegram_id, rol, contenido
    db.add(Mensaje(telegram_id=chat_id, rol="usuario", contenido=texto_usuario))
    db.commit()

    # 3. Memoria Conversacional (Últimos 6 mensajes)
    ultimos_mensajes = db.query(Mensaje)\
        .filter(Mensaje.telegram_id == chat_id)\
        .order_by(Mensaje.id.desc())\
        .limit(6)\
        .all()
    ultimos_mensajes.reverse()

    # Formatear el historial leyendo 'rol' y 'contenido'
    historial_formateado = [
        {
            "role": "user" if msg.rol == "usuario" else "assistant", 
            "content": msg.contenido
        } 
        for msg in ultimos_mensajes
    ]

    # 4. Respuesta Inteligente de OpenAI
    respuesta_inteligente = await obtener_respuesta_ia(historial_formateado)

    # 5. Guardar la respuesta del bot en la BD
    db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=respuesta_inteligente))
    db.commit()

    # 6. Enviar a Telegram (Telegram requiere que sea el int original)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id_int, "text": respuesta_inteligente}
    
    # --- PRINTS DE DEBUGGING ---
    print(f"🤖 IA Respondió: {respuesta_inteligente}")
    print(f"🔑 Token cargado: {'Sí' if TELEGRAM_TOKEN else 'No'}")
    
    async with httpx.AsyncClient() as client:
        respuesta_telegram = await client.post(url, json=payload)
        
        # Ver qué nos contesta Telegram al intentar enviarle el mensaje
        print(f"📡 Estatus Telegram: {respuesta_telegram.status_code}")
        print(f"📄 Detalle Telegram: {respuesta_telegram.text}")

    return {"status": "ok"}