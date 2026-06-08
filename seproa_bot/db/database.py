from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de la base de datos local SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./seproa_bot.db"

# Creación del motor. busy_timeout ayuda a manejar bloqueos concurrentes.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 60} 
)

# --- OPTIMIZACIÓN EXTREMA DE CONCURRENCIA PARA SQLITE ---
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Write-Ahead Logging permite leer mientras se escribe de forma robusta
    cursor.execute("PRAGMA journal_mode=WAL")
    # OFF acelera drásticamente las escrituras al no esperar confirmación física inmediata
    cursor.execute("PRAGMA synchronous=OFF")
    # Mantiene los datos en RAM más tiempo
    cursor.execute("PRAGMA cache_size=-64000")
    # Reintento automático de 60s antes de lanzar "Database is locked"
    cursor.execute("PRAGMA busy_timeout=60000")
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