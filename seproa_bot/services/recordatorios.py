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
    Busca citas con estado 'Confirmada' que ocurren en las próximas 24-26 horas,
    envía recordatorios y cambia su estado a 'Recordada' si se envía al menos por un medio.
    """
    print("⏰ [SCHEDULER] Iniciando ciclo de recordatorios robusto...")
    db = SessionLocal()
    try:
        ahora = datetime.now()
        # Ventana ampliada: 23h a 26h para evitar perder citas por retrasos del servidor
        inicio_ventana = ahora + timedelta(hours=23)
        fin_ventana = ahora + timedelta(hours=26)

        citas_a_recordar = db.query(Cita).filter(
            Cita.fecha_hora >= inicio_ventana,
            Cita.fecha_hora <= fin_ventana,
            Cita.estado == "Confirmada"
        ).all()

        if not citas_a_recordar:
            print("⏰ [SCHEDULER] No hay citas pendientes.")
            return

        config = db.query(ConfiguracionBot).first()
        ubicacion = config.ubicacion_contacto if config and config.ubicacion_contacto else "Nuestras oficinas"

        async with httpx.AsyncClient() as client:
            for cita in citas_a_recordar:
                usuario = db.query(Usuario).filter(Usuario.id == cita.usuario_id).first()
                if not usuario: continue

                fecha_str = cita.fecha_hora.strftime('%d/%m/%Y')
                hora_str = cita.fecha_hora.strftime('%H:%M')

                envio_exitoso = False

                # 1. Intentar Telegram
                try:
                    mensaje_tg = f"⏰ **¡RECORDATORIO DE CITA!**\n\nHola, te recordamos que tienes una asesoría de **{cita.tipo_servicio}** mañana.\n\n📅 **Fecha:** {fecha_str}\n⏰ **Hora:** {hora_str}\n📍 **Lugar:** {ubicacion}"
                    resp = await client.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                                             json={"chat_id": usuario.telegram_id, "text": mensaje_tg, "parse_mode": "Markdown"}, timeout=10)
                    if resp.status_code == 200:
                        envio_exitoso = True
                        print(f"✅ Telegram enviado a {usuario.telegram_id}")
                except Exception as e:
                    print(f"⚠️ Error Telegram recordatorio: {e}")

                # 2. Intentar Correo
                if cita.email_usuario:
                    try:
                        success_mail = await asyncio.to_thread(
                            _enviar_correo_sync, 
                            cita.email_usuario, fecha_str, hora_str, 
                            f"RECORDATORIO: {cita.tipo_servicio}", ubicacion
                        )
                        if success_mail:
                            envio_exitoso = True
                            print(f"✅ Correo enviado a {cita.email_usuario}")
                    except Exception as e:
                        print(f"⚠️ Error Correo recordatorio: {e}")

                # 3. Marcar como Recordada si al menos uno funcionó
                if envio_exitoso:
                    cita.estado = "Recordada"
                    db.add(cita)
                    print(f"📌 Cita {cita.id} marcada como 'Recordada'.")

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"❌ [SCHEDULER] Error crítico: {e}")
    finally:
        db.close()