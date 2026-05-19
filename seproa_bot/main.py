from fastapi import FastAPI
from db.database import engine, Base
# Importamos el router que acabamos de crear
from bot.telegram_bot import router as bot_router

# Crear las tablas en la BD si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SEPROA Chatbot Empresarial")

# Conectamos las rutas del bot a nuestra aplicación principal
app.include_router(bot_router)

@app.get("/")
async def root():
    return {"message": "Servidor SEPROA activo y listo."}