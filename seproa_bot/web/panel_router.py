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

def render_with_layout(request: Request, name: str, context: dict):
    """
    Función auxiliar para devolver el fragmento si es una petición HTMX,
    o la página completa (dashboard) si es una carga directa del navegador.
    """
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name=name, context=context)
    
    # Si es carga directa, cargamos el dashboard y le decimos qué contenido inyectar al inicio
    context["child_template"] = name
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)

@router.get("/")
def dashboard_principal(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@router.get("/conversaciones")
def lista_conversaciones(request: Request, db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).order_by(Usuario.id.desc()).all()
    return render_with_layout(request, "conversaciones.html", {"usuarios": usuarios})

@router.get("/config")
def ver_panel(request: Request, db: Session = Depends(get_db)):
    orden_dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    horarios_raw = db.query(HorarioAtencion).all()
    horarios_ordenados = sorted(horarios_raw, key=lambda x: (orden_dias.get(x.dia_semana, 99), x.hora_inicio))

    context = {
        "config": db.query(ConfiguracionBot).first(),
        "tonos": db.query(Tono).all(),
        "servicios": db.query(Servicio).all(),
        "faqs": db.query(PreguntaFrecuente).all(),
        "horarios": horarios_ordenados
    }
    return render_with_layout(request, "config.html", context)

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
    
    # Ordenar horarios: Lunes a Domingo y por Hora de inicio
    orden_dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    horarios_ordenados = sorted(horarios_db, key=lambda x: (orden_dias.get(x.dia_semana, 99), x.hora_inicio))

    arr_horarios = []
    for h in horarios_ordenados:
        if h.es_laboral and h.hora_inicio and h.hora_fin:
            arr_horarios.append(f"- {h.dia_semana}: {h.hora_inicio.strftime('%H:%M')} a {h.hora_fin.strftime('%H:%M')}")
        else:
            arr_horarios.append(f"- {h.dia_semana}: Cerrado")
    txt_horarios = "\n".join(arr_horarios) or "Horarios no definidos."

    validar_y_reconstruir_prompt(config, txt_servicios, txt_faqs, txt_horarios)

@router.post("/config/save")
def guardar_configuracion(
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
def handle_add_servicio(nombre: str = Form(...), descripcion: str = Form(...), db: Session = Depends(get_db)):
    services.agregar(db, nombre, descripcion)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/servicios/delete/{id}")
def handle_del_servicio(id: int, db: Session = Depends(get_db)):
    services.eliminar(db, id)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/horarios/add")
def handle_add_horario(dia: str = Form(...), inicio: str = Form(...), fin: str = Form(...), db: Session = Depends(get_db)):
    success, msg = horarios.agregar(db, dia, inicio, fin)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/horarios/delete/{id}")
def handle_del_horario(id: int, db: Session = Depends(get_db)):
    horarios.eliminar(db, id)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/faqs/add")
def handle_add_faq(pregunta: str = Form(...), respuesta: str = Form(...), db: Session = Depends(get_db)):
    faqs.agregar(db, pregunta, respuesta)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/faqs/delete/{id}")
def handle_del_faq(id: int, db: Session = Depends(get_db)):
    faqs.eliminar(db, id)
    sincronizar_cerebro_bot(db)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.get("/conversaciones/lista-parcial")
def lista_parcial(request: Request, db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).order_by(Usuario.id.desc()).all()
    return templates.TemplateResponse(request=request, name="lista_usuarios.html", context={"usuarios": usuarios})

@router.get("/conversaciones/detalle/{usuario_id}")
def ver_detalle(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return RedirectResponse(url="/admin/conversaciones")
    mensajes = db.query(Mensaje).filter(Mensaje.telegram_id == usuario.telegram_id).order_by(Mensaje.id.desc()).limit(20).all()
    mensajes.reverse()
    return templates.TemplateResponse(request=request, name="chat_detalle.html", context={"usuario": usuario, "mensajes": mensajes})

@router.get("/conversaciones/mensajes/{usuario_id}")
def obtener_solo_mensajes(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario: return ""
    mensajes = db.query(Mensaje).filter(Mensaje.telegram_id == usuario.telegram_id).order_by(Mensaje.id.desc()).limit(20).all()
    mensajes.reverse() 
    return templates.TemplateResponse(request=request, name="mensajes_lista.html", context={"mensajes": mensajes})

async def tarea_enviar_telegram(chat_id: str, mensaje: str, usuario_id: int):
    if not TELEGRAM_TOKEN: return
    url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url_send, json={"chat_id": chat_id, "text": mensaje}, timeout=15.0)
            if resp.status_code == 200:
                await manager.broadcast("update", channel=f"chat_{usuario_id}")
    except Exception as e:
        print(f"❌ Error en Telegram Background Task: {e}")

@router.post("/conversaciones/intervenir/{usuario_id}")
def intervenir(usuario_id: int, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        usuario.esta_intervenido = not usuario.esta_intervenido
        intervenido = usuario.esta_intervenido
        telegram_id = usuario.telegram_id
        db.commit()
        
        html_sidebar = f"""
        <div id="usuario-fila-{usuario_id}" hx-swap-oob="outerHTML" 
             class="p-4 border-b border-gray-100 hover:bg-gray-50 transition cursor-pointer flex justify-between items-center relative group usuario-sidebar-item"
             hx-get="/admin/conversaciones/detalle/{usuario_id}" hx-target="#panel-chat-derecho" hx-swap="innerHTML" hx-indicator="#loading-sidebar-{usuario_id}"
             onclick="desactivarOtrosItems(this)">
            <div class="flex-1 min-w-0 mr-2">
                <p class="font-medium text-gray-800 truncate">ID: {telegram_id}</p>
                <p class="text-xs text-gray-500 truncate italic">Ver conversación...</p>
            </div>
            <div class="flex items-center space-x-2">
                <div id="loading-sidebar-{usuario_id}" class="htmx-indicator"><svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-opacity-10 {'bg-green-100 text-green-800' if not intervenido else 'bg-red-100 text-red-800'}">
                    ● {'IA' if not intervenido else 'Humano'}
                </span>
            </div>
        </div>
        """
        background_tasks.add_task(manager.broadcast, html_sidebar, "global")
        background_tasks.add_task(manager.broadcast, "update", f"chat_{usuario_id}")
        
    return ver_detalle(usuario_id, request, db)

@router.post("/conversaciones/enviar-mensaje")
def enviar_mensaje_humano(request: Request, background_tasks: BackgroundTasks, chat_id: str = Form(...), mensaje: str = Form(...), db: Session = Depends(get_db)):
    try:
        usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
        if not usuario: return RedirectResponse(url="/admin/conversaciones", status_code=303)
        db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=f"[HUMANO]: {mensaje}"))
        db.commit()
        background_tasks.add_task(tarea_enviar_telegram, chat_id, mensaje, usuario.id)
        
        html_mensaje = f'<div id="contenedor-mensajes-lista" hx-swap-oob="beforeend"><div class="flex flex-col items-end"><div class="max-w-md px-4 py-2 rounded-lg shadow-sm text-sm bg-blue-600 text-white rounded-br-none">[HUMANO]: {mensaje}</div><span class="text-xxs text-gray-400 mt-1 px-1">Rol: bot</span></div></div>'
        preview = f"[HUMANO]: {mensaje}"[:30] + "..."
        html_sidebar = f"""
        <div id="usuario-fila-{usuario.id}" hx-swap-oob="outerHTML" 
             class="p-4 border-b border-gray-100 hover:bg-gray-50 transition cursor-pointer flex justify-between items-center relative group usuario-sidebar-item"
             hx-get="/admin/conversaciones/detalle/{usuario.id}" hx-target="#panel-chat-derecho" hx-swap="innerHTML" hx-indicator="#loading-sidebar-{usuario.id}"
             onclick="desactivarOtrosItems(this)">
            <div class="flex-1 min-w-0 mr-2">
                <p class="font-medium text-gray-800 truncate">ID: {chat_id}</p>
                <p class="text-xs text-gray-400 truncate">{preview}</p>
            </div>
            <div class="flex items-center space-x-2">
                <div id="loading-sidebar-{usuario.id}" class="htmx-indicator"><svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-opacity-10 {'bg-green-100 text-green-800' if not usuario.esta_intervenido else 'bg-red-100 text-red-800'}">
                    ● {'IA' if not usuario.esta_intervenido else 'Humano'}
                </span>
            </div>
        </div>
        """
        background_tasks.add_task(manager.broadcast, html_mensaje, f"chat_{usuario.id}")
        background_tasks.add_task(manager.broadcast, html_sidebar, "global")
        return ver_detalle(usuario.id, request, db)
    except Exception as e:
        db.rollback()
        print(f"❌ Error al enviar mensaje: {e}")
        usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
        return ver_detalle(usuario.id, request, db) if usuario else RedirectResponse(url="/admin/conversaciones", status_code=303)
