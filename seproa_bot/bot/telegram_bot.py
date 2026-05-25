import os
import httpx
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from db.database import get_db
from db.models import Usuario, Mensaje, ConfiguracionBot, Servicio, PreguntaFrecuente, HorarioAtencion
from services.openai_service import obtener_respuesta_ia

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    if "message" not in data: return {"status": "ok"}
    chat_id_int = data["message"]["chat"]["id"]
    chat_id = str(chat_id_int) 
    texto_usuario = data["message"].get("text", "")
    if not texto_usuario: return {"status": "ok"}

    usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
    if not usuario:
        usuario = Usuario(telegram_id=chat_id)
        db.add(usuario)
        db.commit()

    db.add(Mensaje(telegram_id=chat_id, rol="usuario", contenido=texto_usuario))
    db.commit()

    config = db.query(ConfiguracionBot).first()
    
    # Extraer catálogos
    servicios_db = db.query(Servicio).all()
    faqs_db = db.query(PreguntaFrecuente).all()
    horarios_db = db.query(HorarioAtencion).all()

    lista_servicios = "\n".join([f"- {s.nombre}: {s.descripcion}" for s in servicios_db]) or "Sin servicios registrados."
    lista_faqs = "\n\n".join([f"P: {f.pregunta}\nR: {f.respuesta}" for f in faqs_db]) or "Sin FAQs registradas."
    
    horarios_str = []
    for h in horarios_db:
        if h.es_laboral and h.hora_inicio and h.hora_fin:
            horarios_str.append(f"{h.dia_semana}: {h.hora_inicio.strftime('%H:%M')} a {h.hora_fin.strftime('%H:%M')}")
        else:
            horarios_str.append(f"{h.dia_semana}: Cerrado")
    lista_horarios = "\n".join(horarios_str) or "Horarios no definidos."

    t_etiqueta = config.tono.etiqueta if config and config.tono else "Formal"
    t_desc = config.tono.descripcion if config and config.tono else "Lenguaje profesional."

    ultimos = db.query(Mensaje).filter(Mensaje.telegram_id == chat_id).order_by(Mensaje.id.desc()).limit(6).all()
    ultimos.reverse()
    historial = [{"role": "user" if m.rol == "usuario" else "assistant", "content": m.contenido} for m in ultimos]

    respuesta_ia = await obtener_respuesta_ia(
        historial, config, t_etiqueta, t_desc, lista_servicios, lista_faqs, lista_horarios
    )

    db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=respuesta_ia))
    db.commit()

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id_int, "text": respuesta_ia})

    return {"status": "ok"}