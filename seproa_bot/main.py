# main.py
from fastapi import FastAPI
from db.database import engine, Base, SessionLocal
from bot.telegram_bot import router as bot_router
from web.panel_router import router as panel_router

# Servicios e Imports de optimización
from services.seeder_service import precargar_datos
from services.openai_service import validar_y_reconstruir_prompt
from db.models import ConfiguracionBot, Servicio, PreguntaFrecuente, HorarioAtencion

# 1. Crear las tablas en la BD si no existen al iniciar
Base.metadata.create_all(bind=engine)

# 2. PROCESO MAESTRO: Precargado físico + Sembrado de memoria RAM (Caché)
db = SessionLocal()
try:
    # A) Precargado tradicional en la BD física
    precargar_datos(db)
    
    # B) Inmediatamente después, consultamos los datos frescos (ya precargados o editados)
    config_db = db.query(ConfiguracionBot).first()
    servicios_db = db.query(Servicio).all()
    faqs_db = db.query(PreguntaFrecuente).all()
    horarios_db = db.query(HorarioAtencion).all()

    # C) Formateamos los catálogos en texto plano esbelto para la IA
    txt_servicios = "\n".join([f"• {s.nombre}: {s.descripcion.strip()}" for s in servicios_db]) or "Sin servicios registrados."
    txt_faqs = "\n\n".join([f"P: {f.pregunta}\nR: {f.respuesta}" for f in faqs_db]) or "Sin FAQs registradas."
    
    arr_horarios = []
    for h in horarios_db:
        if h.es_laboral and h.hora_inicio and h.hora_fin:
            arr_horarios.append(f"- {h.dia_semana}: {h.hora_inicio.strftime('%H:%M')} a {h.hora_fin.strftime('%H:%M')}")
        else:
            arr_horarios.append(f"- {h.dia_semana}: Cerrado")
    txt_horarios = "\n".join(arr_horarios) or "Horarios no definidos."

    # D) FORZAMOS la carga por defecto a la RAM global del proceso
    validar_y_reconstruir_prompt(config_db, txt_servicios, txt_faqs, txt_horarios)
    print("✅ [BOOT] Base de datos sembrada y Memoria Caché inicializada con éxito para SEPROA.")

except Exception as e:
    print(f"⚠️ Error crítico durante el arranque o inicialización de caché: {e}")
finally:
    db.close() # Cierre seguro de la conexión inicial

# 3. Inicializar la aplicación de FastAPI
app = FastAPI(title="SEPROA Chatbot Empresarial")

# Conectamos las rutas de los módulos individuales
app.include_router(bot_router)
app.include_router(panel_router)

@app.get("/")
async def root():
    return {"message": "Servidor SEPROA activo, caché sincronizada y listo."}