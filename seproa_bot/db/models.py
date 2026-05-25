from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Time, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)


class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, ForeignKey("usuarios.telegram_id"))
    rol = Column(String) # 'usuario' o 'bot'
    contenido = Column(Text)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

# Configuración del bot para personalizar su comportamiento y respuestas
class Tono(Base):
    __tablename__ = "tonos"
    id = Column(Integer, primary_key=True, index=True)
    etiqueta = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)

class HorarioAtencion(Base):
    __tablename__ = "horarios"
    id = Column(Integer, primary_key=True, index=True)
    dia_semana = Column(String, nullable=False)
    hora_inicio = Column(Time, nullable=True)
    hora_fin = Column(Time, nullable=True)
    es_laboral = Column(Boolean, default=True)

class Servicio(Base):
    __tablename__ = "servicios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)

class PreguntaFrecuente(Base):
    __tablename__ = "preguntas_frecuentes"
    id = Column(Integer, primary_key=True, index=True)
    pregunta = Column(String, nullable=False)
    respuesta = Column(Text, nullable=False)


class ConfiguracionBot(Base):
    __tablename__ = "configuracion_bot"

    id = Column(Integer, primary_key=True, index=True)
    tono_id = Column(Integer, ForeignKey("tonos.id"), nullable=True)
    usa_emojis = Column(Boolean, default=True)
    mensaje_saludo = Column(Text, default="¡Hola! Soy el asistente virtual de SEPROA. ¿En qué puedo ayudarte hoy?")
    mensaje_despedida = Column(Text, default="¡Gracias por contactar a SEPROA! Que tengas un excelente día.")
    correo_contacto = Column(String, default="seproa@outlook.com")
    telefono_contacto = Column(String, default="9991014193")
    ubicacion_contacto = Column(Text, default="Calle 65a No. 264, Residencial Floresta, Mérida, Yucatán, CP 97302")

    # --- MODO VACACIONES ---
    modo_vacaciones = Column(Boolean, default=False)
    fecha_regreso = Column(Date, nullable=True)

    tono = relationship("Tono", foreign_keys=[tono_id])