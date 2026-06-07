import os
import httpx
from fastapi import APIRouter, Request
from db.database import SessionLocal
from db.models import Usuario, Mensaje
from services.openai_service import obtener_respuesta_ia_optimizada
from dotenv import load_dotenv
from services.websocket_manager import manager
from bot.orquestador import procesar_intencion
from datetime import datetime

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

router = APIRouter()
http_client = httpx.AsyncClient()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" not in data: 
        return {"status": "ok"}
        
    chat_id_int = data["message"]["chat"]["id"]
    chat_id = str(chat_id_int) 
    texto_usuario = data["message"].get("text", "")
    
    if not texto_usuario: 
        return {"status": "ok"}

    # Feedback visual "escribiendo"
    url_action = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"
    try:
        await http_client.post(url_action, json={"chat_id": chat_id_int, "action": "typing"})
    except Exception:
        pass

    db = SessionLocal()
    es_nuevo_usuario = False
    
    try:
        # 2. Controlar usuario
        usuario = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
        if not usuario:
            usuario = Usuario(telegram_id=chat_id)
            db.add(usuario)
            db.flush()
            es_nuevo_usuario = True

        # 3. Registrar mensaje usuario
        db.add(Mensaje(telegram_id=chat_id, rol="usuario", contenido=texto_usuario))
        db.commit()

        # 🔥 ACTUALIZACIÓN OOB: El administrador ve el mensaje del usuario instantáneamente
        html_mensaje = f"""
        <div id="contenedor-mensajes-lista" hx-swap-oob="beforeend">
            <div class="flex flex-col items-start">
                <div class="max-w-md px-4 py-2 rounded-lg shadow-sm text-sm bg-white text-gray-800 rounded-bl-none border border-gray-200">
                    {texto_usuario}
                </div>
                <span class="text-xxs text-gray-400 mt-1 px-1">Rol: usuario</span>
            </div>
        </div>
        """
        await manager.broadcast(html_mensaje, channel=f"chat_{usuario.id}")
        await manager.broadcast("update", channel="global")

        if usuario.esta_intervenido:
            print(f"🚨 [INTERVENCIÓN] Usuario {chat_id} está bajo control humano. Bloqueando IA.")
            return {"status": "ok"}

        # ⏳ RETRASO ESTRATÉGICO: Damos 2 segundos al administrador para leer e intervenir si lo desea
        import asyncio
        await asyncio.sleep(2)
        
        # RE-VALIDACIÓN DE INTERVENCIÓN (Post-espera)
        db.refresh(usuario)
        if usuario.esta_intervenido:
            print(f"🚨 [INTERVENCIÓN] El administrador tomó el control durante la espera. Cancelando IA.")
            return {"status": "ok"}

        # 4. Extraer historial corto para la IA
        ultimos = db.query(Mensaje).filter(Mensaje.telegram_id == chat_id).order_by(Mensaje.id.desc()).limit(4).all()
        ultimos.reverse()
        historial = [{"role": "user" if m.rol == "usuario" else "assistant", "content": m.contenido} for m in ultimos]

        # 5. Procesar con Orquestador
        respuesta_final, accion, datos_json, nuevo_estado = await procesar_intencion(
            texto_usuario, 
            historial, 
            es_nuevo_usuario, 
            chat_id,
            usuario.estado_conversacion,
            db
        )

        # FINAL CHECK: ¿Intervino mientras la IA generaba la respuesta?
        db.refresh(usuario)
        if usuario.esta_intervenido:
            print(f"🚨 [INTERVENCIÓN] El administrador tomó el control durante la generación. Descartando respuesta de IA.")
            return {"status": "ok"}

        if nuevo_estado and nuevo_estado != usuario.estado_conversacion:
            usuario.estado_conversacion = nuevo_estado

        # Acciones especiales
        if accion == "enviar_mapa" or accion == "guardar_cita_db":
            url_location = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendLocation"
            await http_client.post(url_location, json={
                "chat_id": chat_id_int, "latitude": 21.0136630685485, "longitude": -89.55584020754324
            })
        
        if accion == "actualizar_clasificacion" and datos_json:
            nuevo_servicio = datos_json.get("servicio_detectado")
            if nuevo_servicio and nuevo_servicio != "General":
                usuario.clasificacion_principal = nuevo_servicio

        if accion == "guardar_cita_db" and datos_json:
            from db.models import Cita
            fecha = datos_json.get("fecha")
            hora = datos_json.get("hora")
            servicio = datos_json.get("servicio_detectado")
            google_id = datos_json.get("google_event_id")
            email = datos_json.get("email")
            
            fecha_hora_obj = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            nueva_cita = Cita(
                usuario_id=usuario.id,
                tipo_servicio=servicio,
                fecha_hora=fecha_hora_obj,
                google_event_id=google_id,
                estado="Confirmada",
                email_usuario=email
            )
            db.add(nueva_cita)

        # 6. Enviar respuesta a Telegram
        url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        await http_client.post(url_send, json={"chat_id": chat_id_int, "text": respuesta_final, "parse_mode": "Markdown"})

        # 7. Guardar respuesta del bot
        db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=respuesta_final))
        db.commit()

        # 🔥 ACTUALIZACIÓN OOB: El administrador ve la respuesta del bot instantáneamente
        html_respuesta = f"""
        <div id="contenedor-mensajes-lista" hx-swap-oob="beforeend">
            <div class="flex flex-col items-end">
                <div class="max-w-md px-4 py-2 rounded-lg shadow-sm text-sm bg-blue-600 text-white rounded-br-none">
                    {respuesta_final}
                </div>
                <span class="text-xxs text-gray-400 mt-1 px-1">Rol: bot</span>
            </div>
        </div>
        """
        await manager.broadcast(html_respuesta, channel=f"chat_{usuario.id}")

    except Exception as e:
        print(f"❌ ERROR WEBHOOK: {e}")
        db.rollback()
    finally:
        db.close()

    return {"status": "ok"}
