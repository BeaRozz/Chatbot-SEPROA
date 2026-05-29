import os
import httpx
from fastapi import APIRouter, Request
from db.database import SessionLocal  # Tu generador de sesiones limpio
from db.models import Usuario, Mensaje
from services.openai_service import obtener_respuesta_ia_optimizada
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

router = APIRouter()

http_client = httpx.AsyncClient()

# Mantenemos exactamente tu ruta original para que Telegram no se pierda
@router.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    # Validaciones anti-errores de Telegram
    if "message" not in data: 
        return {"status": "ok"}
        
    chat_id_int = data["message"]["chat"]["id"]
    chat_id = str(chat_id_int) 
    texto_usuario = data["message"].get("text", "")
    
    if not texto_usuario: 
        return {"status": "ok"}

    # -------------------------------------------------------------
    # OPTIMIZACIÓN UX: Acción Visual "Escribiendo..." de inmediato
    # -------------------------------------------------------------
    url_action = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"
    try:
        # Le avisa al cliente de Telegram que el bot está procesando, reduciendo la percepción de espera
        await http_client.post(url_action, json={"chat_id": chat_id_int, "action": "typing"})
    except Exception as e:
        print(f"⚠️ No se pudo enviar el sendChatAction: {e}")

    # Apertura de sesión síncrona rápida para guardar la entrada    
    db = SessionLocal()
    
    try:
        # 2. Controlar o crear al Usuario
        usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
        if not usuario:
            usuario = Usuario(telegram_id=chat_id)
            db.add(usuario)
            db.commit()

        # 3. Registrar mensaje del usuario en la BD
        db.add(Mensaje(telegram_id=chat_id, rol="usuario", contenido=texto_usuario))
        db.commit()

        # 4. Extraer memoria conversacional compacta (últimos 4 mensajes: 2 de usuario, 2 de bot)
        ultimos = db.query(Mensaje).filter(Mensaje.telegram_id == chat_id).order_by(Mensaje.id.desc()).limit(4).all()
        ultimos.reverse()
        historial = [{"role": "user" if m.rol == "usuario" else "assistant", "content": m.contenido} for m in ultimos]

        # 5. Obtener respuesta de IA usando el prompt cacheado en RAM
        respuesta_ia = await obtener_respuesta_ia_optimizada(historial)

        # Enviar respuesta inmediata por red usando el pool global de httpx
        url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        await http_client.post(url_send, json={"chat_id": chat_id_int, "text": respuesta_ia})

        # Registrar la salida de la IA al final de la transacción
        db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=respuesta_ia))
        db.commit()

    except Exception as e:
        print(f"❌ ERROR EN WEBHOOK: {e}")
        db.rollback()
    finally:
        # 10. CERRAR LA SESIÓN DE FORMA OBLIGATORIA
        db.close()

    return {"status": "ok"}