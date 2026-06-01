from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Time, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

# Tabla de usuarios, cada uno con su telegram_id único y su clasificación de interés más reciente
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)

    #Interés más reciente
    clasificacion_principal = Column(String, default="General")

    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    citas = relationship("Cita", back_populates="usuario")

# Tabla para almacenar citas
class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    # El servicio específico para esta cita individual (Fiscal, Contable, Administrativa, General)
    tipo_servicio = Column(String, nullable=False)
    
    # La fecha y hora acordadas
    fecha_hora = Column(DateTime, nullable=False)
    
    # Guardaremos el ID del evento de Google Calendar para poder cancelarlo o modificarlo después
    google_event_id = Column(String, nullable=True) 
    
    # Pendiente, Confirmada, Cancelada
    estado = Column(String, default="Pendiente") 
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa
    usuario = relationship("Usuario", back_populates="citas")

# Tabla de mensajes
class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, ForeignKey("usuarios.telegram_id"), index=True)
    rol = Column(String) # 'usuario' o 'bot'
    contenido = Column(Text)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

# Configuración del bot para personalizar su comportamiento y respuestas
class Tono(Base):
    __tablename__ = "tonos"
    id = Column(Integer, primary_key=True, index=True)
    etiqueta = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)

# Horarios de atención para informar al usuario si el bot está disponible o no, y cuándo lo estará
class HorarioAtencion(Base):
    __tablename__ = "horarios"
    id = Column(Integer, primary_key=True, index=True)
    dia_semana = Column(String, nullable=False)
    hora_inicio = Column(Time, nullable=True)
    hora_fin = Column(Time, nullable=True)
    es_laboral = Column(Boolean, default=True)

# Tabla de servicios disponibles
class Servicio(Base):
    __tablename__ = "servicios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)

# Tabla de preguntas frecuentes
class PreguntaFrecuente(Base):
    __tablename__ = "preguntas_frecuentes"
    id = Column(Integer, primary_key=True, index=True)
    pregunta = Column(String, nullable=False)
    respuesta = Column(Text, nullable=False)

# Tabla de configuración general del bot, incluyendo mensajes predeterminados, contacto y modo vacaciones
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