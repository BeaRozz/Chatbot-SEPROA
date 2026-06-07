from datetime import date
import os
import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Form, Request, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import ConfiguracionBot, Mensaje, Tono, Servicio, PreguntaFrecuente, HorarioAtencion, Usuario
from services.cruds import horarios, services, faqs
from services.openai_service import validar_y_reconstruir_prompt
from services.websocket_manager import manager

router = APIRouter(prefix="/admin", tags=["Panel Web"])
templates = Jinja2Templates(directory="templates")

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

@router.get("/")
async def dashboard_principal():
    return {"vista": "Configuración del Bot", "tabs": ["Configuración", "Conversaciones"]}

@router.get("/conversaciones")
async def lista_conversaciones(request: Request, db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return templates.TemplateResponse(
        request=request, 
        name="conversaciones.html", 
        context={"usuarios": usuarios}
    )

@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        print(f"⚠️ Error en WebSocket {channel}: {e}")
        manager.disconnect(websocket, channel)

def sincronizar_cerebro_bot(db: Session):
    config = db.query(ConfiguracionBot).first()
    servicios_db = db.query(Servicio).all()
    faqs_db = db.query(PreguntaFrecuente).all()
    horarios_db = db.query(HorarioAtencion).all()

    txt_servicios = "\n".join([f"• {s.nombre}: {s.descripcion.strip()}" for s in servicios_db]) or "Sin servicios registrados."
    txt_faqs = "\n\n".join([f"P: {f.pregunta}\nR: {f.respuesta}" for f in faqs_db]) or "Sin FAQs registradas."
    
    arr_horarios = []
    for h in horarios_db:
        if h.es_laboral and h.hora_inicio and h.hora_fin:
            arr_horarios.append(f"- {h.dia_semana}: {h.hora_inicio.strftime('%H:%M')} a {h.hora_fin.strftime('%H:%M')}")
        else:
            arr_horarios.append(f"- {h.dia_semana}: Cerrado")
    txt_horarios = "\n".join(arr_horarios) or "Horarios no definidos."

    validar_y_reconstruir_prompt(config, txt_servicios, txt_faqs, txt_horarios)

@router.get("/config")
async def ver_panel(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request, name="config.html", context={
            "config": db.query(ConfiguracionBot).first(),
            "tonos": db.query(Tono).all(),
            "servicios": db.query(Servicio).all(),
            "faqs": db.query(PreguntaFrecuente).all(),
            "horarios": db.query(HorarioAtencion).order_by(HorarioAtencion.id).all()
        }
    )

@router.post("/config/save")
async def guardar_configuracion(
    request: Request,
    tono_id: int = Form(...),
    usa_emojis: bool = Form(None),
    modo_vacaciones: bool = Form(None),
    fecha_regreso: str = Form(None),
    mensaje_saludo: str = Form(...),
    mensaje_despedida: str = Form(...),
    correo_contacto: str = Form(...),
    telefono_contacto: str = Form(...),
    ubicacion_contacto: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        config = db.query(ConfiguracionBot).first()
        if not config:
            config = ConfiguracionBot()
            db.add(config)

        config.tono_id = tono_id
        config.usa_emojis = True if usa_emojis else False
        config.modo_vacaciones = True if modo_vacaciones else False
        config.mensaje_saludo = mensaje_saludo.strip()
        config.mensaje_despedida = mensaje_despedida.strip()
        config.correo_contacto = correo_contacto.strip()
        config.telefono_contacto = telefono_contacto.strip()
        config.ubicacion_contacto = ubicacion_contacto.strip()
        
        if config.modo_vacaciones and fecha_regreso:
            config.fecha_regreso = date.fromisoformat(fecha_regreso)
        else:
            config.fecha_regreso = None
            
        db.commit()
        sincronizar_cerebro_bot(db)
        return RedirectResponse(url="/admin/config?success=1", status_code=303)
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR CRÍTICO AL GUARDAR CONFIGURACIÓN: {e}")
        return RedirectResponse(url="/admin/config?error=1", status_code=303)

@router.post("/servicios/add")
async def handle_add_servicio(nombre: str = Form(...), descripcion: str = Form(...), db: Session = Depends(get_db)):
    services.agregar(db, nombre, descripcion)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/servicios/delete/{id}")
async def handle_del_servicio(id: int, db: Session = Depends(get_db)):
    services.eliminar(db, id)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/horarios/add")
async def handle_add_horario(dia: str = Form(...), inicio: str = Form(...), fin: str = Form(...), db: Session = Depends(get_db)):
    success, msg = horarios.agregar(db, dia, inicio, fin)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/horarios/delete/{id}")
async def handle_del_horario(id: int, db: Session = Depends(get_db)):
    horarios.eliminar(db, id)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/faqs/add")
async def handle_add_faq(pregunta: str = Form(...), respuesta: str = Form(...), db: Session = Depends(get_db)):
    faqs.agregar(db, pregunta, respuesta)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/faqs/delete/{id}")
async def handle_del_faq(id: int, db: Session = Depends(get_db)):
    faqs.eliminar(db, id)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.get("/conversaciones/lista-parcial")
def lista_parcial(request: Request, db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return templates.TemplateResponse(
        request=request, 
        name="lista_usuarios.html", 
        context={"usuarios": usuarios}
    )

@router.get("/conversaciones/detalle/{usuario_id}")
def ver_detalle(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return RedirectResponse(url="/admin/conversaciones")
    mensajes = db.query(Mensaje).filter(Mensaje.telegram_id == usuario.telegram_id).order_by(Mensaje.id.desc()).limit(50).all()
    mensajes.reverse()
    return templates.TemplateResponse(
        request=request, 
        name="chat_detalle.html", 
        context={"usuario": usuario, "mensajes": mensajes}
    )

@router.get("/conversaciones/mensajes/{usuario_id}")
def obtener_solo_mensajes(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return ""
    mensajes = db.query(Mensaje).filter(Mensaje.telegram_id == usuario.telegram_id).order_by(Mensaje.id.desc()).limit(50).all()
    mensajes.reverse() 
    return templates.TemplateResponse(
        request=request, 
        name="mensajes_lista.html", 
        context={"mensajes": mensajes}
    )

async def tarea_enviar_telegram(chat_id: str, mensaje: str, usuario_id: int):
    if not TELEGRAM_TOKEN:
        return
    url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url_send, json={"chat_id": chat_id, "text": mensaje}, timeout=15.0)
            if resp.status_code == 200:
                await manager.broadcast("update", channel=f"chat_{usuario_id}")
    except Exception as e:
        print(f"❌ Error en Telegram Background Task: {e}")

@router.post("/conversaciones/intervenir/{usuario_id}")
async def intervenir(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        usuario.esta_intervenido = not usuario.esta_intervenido
        db.commit()
    return ver_detalle(usuario_id, request, db)

@router.post("/conversaciones/enviar-mensaje")
async def enviar_mensaje_humano(
    request: Request,
    background_tasks: BackgroundTasks,
    chat_id: str = Form(...), 
    mensaje: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
        if not usuario:
            return RedirectResponse(url="/admin/conversaciones", status_code=303)
        
        db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=f"[HUMANO]: {mensaje}"))
        db.commit()
        
        background_tasks.add_task(tarea_enviar_telegram, chat_id, mensaje, usuario.id)
        
        await manager.broadcast("update", channel=f"chat_{usuario.id}")
        await manager.broadcast("update", channel="global")
        
        return ver_detalle(usuario.id, request, db)
    except Exception as e:
        db.rollback()
        print(f"❌ Error al enviar mensaje: {e}")
        usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
        if usuario:
            return ver_detalle(usuario.id, request, db)
        return RedirectResponse(url="/admin/conversaciones", status_code=303)
