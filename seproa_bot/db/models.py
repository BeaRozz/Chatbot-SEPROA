from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    # Aquí podrán agregar luego campos como 'tipo_cliente', 'bloqueado', etc.

class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, ForeignKey("usuarios.telegram_id"))
    rol = Column(String) # 'usuario' o 'bot'
    contenido = Column(Text)
    fecha = Column(DateTime(timezone=True), server_default=func.now())