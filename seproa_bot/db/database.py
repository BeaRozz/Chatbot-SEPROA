from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de la base de datos local SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./seproa_bot.db"

# Creación del motor. connect_args es necesario solo para SQLite en FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 30} 
)

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