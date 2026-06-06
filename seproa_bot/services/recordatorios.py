import os
import httpx
import asyncio
from datetime import datetime, timedelta
from db.database import SessionLocal
from db.models import Cita, Usuario, ConfiguracionBot
from services.email_service import _enviar_correo_sync
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def procesar_recordatorios_24h():
    """
    Busca citas con estado 'Confirmada' que ocurren en las próximas 24 horas,
    envía recordatorios y cambia su estado a 'Recordada' para evitar duplicados.
    """
    print("⏰ [SCHEDULER] Iniciando ciclo de recordatorios...")
    db = SessionLocal()
    try:
        ahora = datetime.now()
        # Ventana objetivo: Citas que ocurren en el rango de 24h a 24.5h a partir de ahora
        inicio_ventana = ahora + timedelta(hours=23)
        fin_ventana = ahora + timedelta(hours=24, minutes=30)

        # 1. Consultar citas confirmadas pendientes de recordar
        citas_a_recordar = db.query(Cita).filter(
            Cita.fecha_hora >= inicio_ventana,
            Cita.fecha_hora <= fin_ventana,
            Cita.estado == "Confirmada"
        ).all()

        if not citas_a_recordar:
            print("⏰ [SCHEDULER] No hay citas pendientes de recordatorio.")
            return

        config = db.query(ConfiguracionBot).first()
        ubicacion = config.ubicacion_contacto if config and config.ubicacion_contacto else "Nuestras oficinas"

        async with httpx.AsyncClient() as client:
            for cita in citas_a_recordar:
                usuario = db.query(Usuario).filter(Usuario.id == cita.usuario_id).first()
                if not usuario or not usuario.telegram_id: 
                    continue
                
                fecha_str = cita.fecha_hora.strftime('%d/%m/%Y')
                hora_str = cita.fecha_hora.strftime('%H:%M')

                # 2. Intentar envío por Telegram
                mensaje_tg = (
                    f"⏰ **¡RECORDATORIO DE CITA!**\n\n"
                    f"Hola, te recordamos que tienes una asesoría de **{cita.tipo_servicio}** mañana.\n\n"
                    f"📅 **Fecha:** {fecha_str}\n"
                    f"⏰ **Hora:** {hora_str}\n"
                    f"📍 **Lugar:** {ubicacion}\n\n"
                    f"¡Te esperamos con gusto!"
                )
                
                url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                resp = await client.post(url_tg, json={"chat_id": usuario.telegram_id, "text": mensaje_tg, "parse_mode": "Markdown"})
                
                if resp.status_code == 200:
                    # 3. Intentar envío por Correo
                    correo_cliente = cita.email_usuario
                    print(f"📧 Intentando enviar recordatorio por correo a {correo_cliente} para cita {cita.id}...")
                    if correo_cliente:
                        await asyncio.to_thread(
                            _enviar_correo_sync, 
                            correo_cliente, fecha_str, hora_str, 
                            f"RECORDATORIO: {cita.tipo_servicio}", ubicacion
                        )
                    
                    # 4. 🔥 CAMBIO DE ESTADO (La cita ya fue recordada)
                    cita.estado = "Recordada"
                    db.add(cita) # Marcamos para actualizar
                    print(f"✅ Cita {cita.id} notificada y marcada como 'Recordada'.")
                else:
                    print(f"❌ Falló Telegram para cita {cita.id}, estado: {resp.status_code}")

        # Guardamos todos los cambios de estado en un solo commit
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"❌ [SCHEDULER] Error crítico: {e}")
    finally:
        db.close()