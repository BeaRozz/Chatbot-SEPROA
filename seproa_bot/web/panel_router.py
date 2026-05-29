from datetime import date

from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import ConfiguracionBot, Tono, Servicio, PreguntaFrecuente, HorarioAtencion
from services.cruds import horarios, services, faqs

router = APIRouter(prefix="/admin", tags=["Panel Web"])
templates = Jinja2Templates(directory="templates")

@router.get("/config")
async def ver_panel(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request, name="config.html", context={
            "config": db.query(ConfiguracionBot).first(),
            "tonos": db.query(Tono).all(),
            "servicios": db.query(Servicio).all(),
            "faqs": db.query(PreguntaFrecuente).all(),
            "horarios": db.query(HorarioAtencion).order_by(HorarioAtencion.dia_semana).all()
        }
    )

@router.post("/config/save")
async def guardar_configuracion(
    request: Request,
    tono_id: int = Form(...),
    usa_emojis: bool = Form(None),
    modo_vacaciones: bool = Form(None),
    fecha_regreso: date = Form(None),
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

        # Asignación de valores controlando los booleanos del HTML
        config.tono_id = tono_id
        config.usa_emojis = True if usa_emojis else False
        config.modo_vacaciones = True if modo_vacaciones else False
        
        # Guardar textos obligatorios y nuevos campos de contacto
        config.mensaje_saludo = mensaje_saludo.strip()
        config.mensaje_despedida = mensaje_despedida.strip()
        config.correo_contacto = correo_contacto.strip()
        config.telefono_contacto = telefono_contacto.strip()
        config.ubicacion_contacto = ubicacion_contacto.strip()
        
        # Validar y procesar la fecha de regreso si está en modo vacaciones
        if config.modo_vacaciones and fecha_regreso:
            config.fecha_regreso = date.fromisoformat(fecha_regreso)
        else:
            config.fecha_regreso = None
            
        db.commit()
        # Redirección limpia indicando éxito por parámetro en la URL
        return RedirectResponse(url="/admin/config?success=1", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"ERROR CRÍTICO AL GUARDAR CONFIGURACIÓN: {e}")
        return RedirectResponse(url="/admin/config?error=1", status_code=303)

@router.post("/servicios/add")
async def handle_add_servicio(nombre: str = Form(...), descripcion: str = Form(...), db: Session = Depends(get_db)):
    services.agregar(db, nombre, descripcion)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/servicios/delete/{id}")
async def handle_del_servicio(id: int, db: Session = Depends(get_db)):
    services.eliminar(db, id)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/horarios/add")
async def handle_add_horario(dia: str = Form(...), inicio: str = Form(...), fin: str = Form(...), db: Session = Depends(get_db)):
    success, msg = horarios.agregar(db, dia, inicio, fin)
    # Aquí podrías pasar 'msg' a la vista para mostrar una alerta de error
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/horarios/delete/{id}")
async def handle_del_horario(id: int, db: Session = Depends(get_db)):
    horarios.eliminar(db, id)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/faqs/add")
async def handle_add_faq(pregunta: str = Form(...), respuesta: str = Form(...), db: Session = Depends(get_db)):
    faqs.agregar(db, pregunta, respuesta)
    return RedirectResponse(url="/admin/config", status_code=303)

@router.post("/faqs/delete/{id}")
async def handle_del_faq(id: int, db: Session = Depends(get_db)):
    faqs.eliminar(db, id)
    return RedirectResponse(url="/admin/config", status_code=303)