from fastapi import FastAPI
from db.database import engine, Base, SessionLocal
# Importamos el router que acabamos de crear
from bot.telegram_bot import router as bot_router
from web.panel_router import router as panel_router
from services.seeder_service import precargar_datos

# Crear las tablas en la BD si no existen
Base.metadata.create_all(bind=engine)

db = SessionLocal()
# Precargar datos iniciales
try:
    precargar_datos(db)
finally:
    db.close()

app = FastAPI(title="SEPROA Chatbot Empresarial")

# Conectamos las rutas del bot a nuestra aplicación principal
app.include_router(bot_router)
app.include_router(panel_router)

@app.get("/")
async def root():
    return {"message": "Servidor SEPROA activo y listo."}