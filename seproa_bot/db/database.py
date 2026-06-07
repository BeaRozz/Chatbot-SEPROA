from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de la base de datos local SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./seproa_bot.db"

# Creación del motor. connect_args es necesario solo para SQLite en FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 30} 
)

# --- ACTIVACIÓN DE MODO WAL (Write-Ahead Logging) ---
# Esto permite que los lectores (Panel) no bloqueen a los escritores (Bot)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# Configuración de la sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán los modelos
Base = declarative_base()

# Dependencia para obtener la sesión de la BD en las rutas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()