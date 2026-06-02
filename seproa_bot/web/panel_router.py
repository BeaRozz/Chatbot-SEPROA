from datetime import date
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import ConfiguracionBot, Tono, Servicio, PreguntaFrecuente, HorarioAtencion
from services.cruds import horarios, services, faqs

# Importación de tu módulo de sincronización
from services.openai_service import validar_y_reconstruir_prompt

router = APIRouter(prefix="/admin", tags=["Panel Web"])
templates = Jinja2Templates(directory="templates")

def sincronizar_cerebro_bot(db: Session):
    """
    Función auxiliar para centralizar la consulta de datos frescos de SQLite
    y reconstruir la caché en la memoria RAM de manera instantánea.
    """
    config = db.query(ConfiguracionBot).first()
    servicios_db = db.query(Servicio).all()
    faqs_db = db.query(PreguntaFrecuente).all()
    horarios_db = db.query(HorarioAtencion).all()

    # Formatear catálogos en texto plano minimalista
    txt_servicios = "\n".join([f"• {s.nombre}: {s.descripcion.strip()}" for s in servicios_db]) or "Sin servicios registrados."
    txt_faqs = "\n\n".join([f"P: {f.pregunta}\nR: {f.respuesta}" for f in faqs_db]) or "Sin FAQs registradas."
    
    arr_horarios = []
    for h in horarios_db:
        if h.es_laboral and h.hora_inicio and h.hora_fin:
            arr_horarios.append(f"- {h.dia_semana}: {h.hora_inicio.strftime('%H:%M')} a {h.hora_fin.strftime('%H:%M')}")
        else:
            arr_horarios.append(f"- {h.dia_semana}: Cerrado")
    txt_horarios = "\n".join(arr_horarios) or "Horarios no definidos."

    # Sincronizamos la variable global RAM
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
    fecha_regreso: str = Form(None), # CORRECCIÓN: Recibimos como 'str' para evitar fallos de parseo en FastAPI
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

        # Asignación controlando booleanos
        config.tono_id = tono_id
        config.usa_emojis = True if usa_emojis else False
        config.modo_vacaciones = True if modo_vacaciones else False
        
        # Limpieza de textos obligatorios
        config.mensaje_saludo = mensaje_saludo.strip()
        config.mensaje_despedida = mensaje_despedida.strip()
        config.correo_contacto = correo_contacto.strip()
        config.telefono_contacto = telefono_contacto.strip()
        config.ubicacion_contacto = ubicacion_contacto.strip()
        
        # Procesamiento e inserción de la fecha controlado
        if config.modo_vacaciones and fecha_regreso:
            config.fecha_regreso = date.fromisoformat(fecha_regreso)
        else:
            config.fecha_regreso = None
            
        db.commit() # Guardado físico exitoso

        # -------------------------------------------------------------
        # SINCRONIZACIÓN REACTIVA DE LA RAM
        # -------------------------------------------------------------
        sincronizar_cerebro_bot(db)

        return RedirectResponse(url="/admin/config?success=1", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR CRÍTICO AL GUARDAR CONFIGURACIÓN: {e}")
        return RedirectResponse(url="/admin/config?error=1", status_code=303)


# -------------------------------------------------------------
# SECCIÓN CRUD: Cada cambio de catálogos reconstruye la caché
# -------------------------------------------------------------

@router.post("/servicios/add")
async def handle_add_servicio(nombre: str = Form(...), descripcion: str = Form(...), db: Session = Depends(get_db)):
    services.agregar(db, nombre, descripcion)
    print(f"✅ Servicio '{nombre}' agregado. Sincronizando con el cerebro del bot...")
    sincronizar_cerebro_bot(db) # Alertas dinámicas al bot
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