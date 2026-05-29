import os
import httpx
from fastapi import APIRouter, Request
from db.database import SessionLocal  # Tu generador de sesiones limpio
from db.models import Usuario, Mensaje, ConfiguracionBot, Servicio, PreguntaFrecuente, HorarioAtencion
from services.openai_service import obtener_respuesta_ia
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

router = APIRouter()

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

    # 1. ABRIR SESIÓN LIMPIA EN TIEMPO REAL
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

        # 4. Consultar configuración fresca de la BD
        config = db.query(ConfiguracionBot).first()
        servicios_db = db.query(Servicio).all()
        faqs_db = db.query(PreguntaFrecuente).all()
        horarios_db = db.query(HorarioAtencion).all()

        # 5. Formatear catálogos relacionales a texto plano para el Prompt
        lista_servicios = "\n".join([f"- {s.nombre}: {s.descripcion}" for s in servicios_db]) or "Sin servicios registrados."
        lista_faqs = "\n\n".join([f"P: {f.pregunta}\nR: {f.respuesta}" for f in faqs_db]) or "Sin FAQs registradas."
        
        horarios_str = []
        for h in horarios_db:
            if h.es_laboral and h.hora_inicio and h.hora_fin:
                horarios_str.append(f"{h.dia_semana}: {h.hora_inicio.strftime('%H:%M')} a {h.hora_fin.strftime('%H:%M')}")
            else:
                horarios_str.append(f"{h.dia_semana}: Cerrado")
        lista_horarios = "\n".join(horarios_str) or "Horarios no definidos."

        # Extraer directrices de Tono
        t_etiqueta = config.tono.etiqueta if config and config.tono else "Formal"
        t_desc = config.tono.descripcion if config and config.tono else "Lenguaje profesional."

        # 6. Extraer memoria conversacional (últimos 6 mensajes)
        ultimos = db.query(Mensaje).filter(Mensaje.telegram_id == chat_id).order_by(Mensaje.id.desc()).limit(4).all()
        ultimos.reverse()
        historial = [{"role": "user" if m.rol == "usuario" else "assistant", "content": m.contenido} for m in ultimos]

        # 7. Procesar respuesta en OpenAI
        respuesta_ia = await obtener_respuesta_ia(
            historial, config, t_etiqueta, t_desc, lista_servicios, lista_faqs, lista_horarios
        )

        # 8. ENVIAR RESPUESTA REAL A TELEGRAM VIA HTTPX
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": chat_id_int, "text": respuesta_ia})

        # 9. Guardar respuesta de la IA en la BD
        db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=respuesta_ia))
        db.commit()

    except Exception as e:
        print(f"❌ ERROR EN WEBHOOK: {e}")
        db.rollback()
    finally:
        # 10. CERRAR LA SESIÓN DE FORMA OBLIGATORIA
        db.close()

    return {"status": "ok"}