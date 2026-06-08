import os
import httpx
import asyncio
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

# Funciones auxiliares para ejecutar DB en hilos secundarios
def registrar_usuario_y_mensaje_sync(chat_id, texto):
    db = SessionLocal()
    try:
        es_nuevo = False
        u = db.query(Usuario).filter(Usuario.telegram_id == chat_id).first()
        if not u:
            u = Usuario(telegram_id=chat_id); db.add(u); db.flush(); es_nuevo = True
        db.add(Mensaje(telegram_id=chat_id, rol="usuario", contenido=texto))
        db.commit()
        return u.id, u.esta_intervenido, u.estado_conversacion, es_nuevo
    finally: db.close()

def obtener_contexto_ia_sync(usuario_id, chat_id):
    db = SessionLocal()
    try:
        u = db.query(Usuario).get(usuario_id)
        if not u or u.esta_intervenido: return None
        ultimos = db.query(Mensaje).filter(Mensaje.telegram_id == chat_id).order_by(Mensaje.id.desc()).limit(4).all(); ultimos.reverse()
        historial = [{"role": "user" if m.rol == "usuario" else "assistant", "content": m.contenido} for m in ultimos]
        return historial
    finally: db.close()

def guardar_respuesta_ia_sync(usuario_id, chat_id, respuesta, nuevo_estado, accion, datos_json):
    db = SessionLocal()
    try:
        u = db.query(Usuario).get(usuario_id)
        if not u or u.esta_intervenido: return False
        if nuevo_estado and nuevo_estado != u.estado_conversacion: u.estado_conversacion = nuevo_estado
        db.add(Mensaje(telegram_id=chat_id, rol="bot", contenido=respuesta))
        if accion == "guardar_cita_db" and datos_json:
            from db.models import Cita
            dt_obj = datetime.strptime(f"{datos_json['fecha']} {datos_json['hora']}", "%Y-%m-%d %H:%M")
            db.add(Cita(usuario_id=usuario_id, tipo_servicio=datos_json['servicio_detectado'], fecha_hora=dt_obj, google_event_id=datos_json.get("google_event_id"), estado="Confirmada", email_usuario=datos_json.get("email")))
        db.commit()
        return True
    finally: db.close()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        print(f"📥 [WEBHOOK] Petición recibida: {data}")
        
        if "message" not in data: 
            print("⚠️ [WEBHOOK] No hay 'message' en la data.")
            return {"status": "ok"}
            
        chat_id_int = data["message"]["chat"]["id"]
        chat_id = str(chat_id_int) 
        texto_usuario = data["message"].get("text", "")
        
        if not texto_usuario: 
            print(f"⚠️ [WEBHOOK] Mensaje sin texto de {chat_id}")
            return {"status": "ok"}

        print(f"📨 [WEBHOOK] Procesando mensaje de {chat_id}: '{texto_usuario}'")

        # Feedback visual (No bloqueante)
        asyncio.create_task(http_client.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction", json={"chat_id": chat_id_int, "action": "typing"}))

        # FASE 1: Registro (HILO APARTE)
        print(f"⚙️ [WEBHOOK] Fase 1: Registrando usuario/mensaje para {chat_id}")
        usuario_id, intervenido, estado_conv, es_nuevo_usuario = await asyncio.to_thread(registrar_usuario_y_mensaje_sync, chat_id, texto_usuario)
        print(f"✅ [WEBHOOK] Fase 1 Completada. ID:{usuario_id}, Nuevo:{es_nuevo_usuario}, Intervenido:{intervenido}")

        # Notificación OOB usuario y Sidebar
        html_mensaje = f'<div id="contenedor-mensajes-lista" hx-swap-oob="beforeend"><div class="flex flex-col items-start"><div class="max-w-md px-4 py-2 rounded-lg shadow-sm text-sm bg-white text-gray-800 border">{texto_usuario}</div><span class="text-xxs text-gray-400 mt-1 px-1">Rol: usuario</span></div></div>'
        html_sidebar = f"""<div id="usuario-fila-{usuario_id}" hx-swap-oob="outerHTML" class="p-4 border-b border-gray-100 hover:bg-gray-50 transition cursor-pointer flex justify-between items-center relative group" hx-get="/admin/conversaciones/detalle/{usuario_id}" hx-target="#panel-chat-derecho" hx-swap="innerHTML" hx-indicator="#loading-sidebar-{usuario_id}"><div><p class="font-medium text-gray-800">ID: {chat_id}</p><p class="text-xs text-blue-600 font-bold animate-pulse">Nuevo mensaje...</p></div><div class="flex items-center space-x-2"><div id="loading-sidebar-{usuario_id}" class="htmx-indicator"><svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div><span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-opacity-10 {'bg-green-100 text-green-800' if not intervenido else 'bg-red-100 text-red-800'}">● {'IA' if not intervenido else 'Humano'}</span></div></div>"""
        
        await manager.broadcast(html_mensaje, channel=f"chat_{usuario_id}")
        await manager.broadcast(html_sidebar, channel="global")
        
        if intervenido: 
            print(f"🚨 [WEBHOOK] Usuario {chat_id} intervenido. Fin flujo.")
            return {"status": "ok"}

        # FASE 2: Espera y Contexto (HILO APARTE)
        print(f"⏳ [WEBHOOK] Fase 2: Esperando 2s y obteniendo historial...")
        await asyncio.sleep(2)
        historial = await asyncio.to_thread(obtener_contexto_ia_sync, usuario_id, chat_id)
        if historial is None: 
            print(f"⚠️ [WEBHOOK] Historial nulo para {chat_id}")
            return {"status": "ok"}

        # OpenAI (IA - NO BLOQUEA DB)
        print(f"🧠 [WEBHOOK] Llamando al orquestador (Modo Nuevo: {es_nuevo_usuario})...")
        # El orquestador ahora maneja sus propias sesiones cortas para lecturas
        respuesta_final, accion, datos_json, nuevo_estado = await procesar_intencion(
            texto_usuario, historial, es_nuevo_usuario, chat_id, estado_conv
        )
        print(f"🤖 [WEBHOOK] Respuesta IA lista.")
        # FASE 3: Guardar y Telegram (HILO APARTE)
        exito = await asyncio.to_thread(guardar_respuesta_ia_sync, usuario_id, chat_id, respuesta_final, nuevo_estado, accion, datos_json)
        if not exito: return {"status": "ok"}

        # Enviar a Telegram
        await http_client.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": chat_id_int, "text": respuesta_final, "parse_mode": "Markdown"})

        # Limpiar Sidebar OOB y mostrar fragmento de respuesta
        preview = (respuesta_final[:30] + '...') if len(respuesta_final) > 30 else respuesta_final
        html_sidebar_final = f"""
        <div id="usuario-fila-{usuario_id}" hx-swap-oob="outerHTML" class="p-4 border-b border-gray-100 hover:bg-gray-50 transition cursor-pointer flex justify-between items-center relative group" hx-get="/admin/conversaciones/detalle/{usuario_id}" hx-target="#panel-chat-derecho" hx-swap="innerHTML" hx-indicator="#loading-sidebar-{usuario_id}">
            <div class="flex-1 min-w-0 mr-2">
                <p class="font-medium text-gray-800 truncate">ID: {chat_id}</p>
                <p class="text-xs text-gray-400 truncate">{preview}</p>
            </div>
            <div class="flex items-center space-x-2">
                <div id="loading-sidebar-{usuario_id}" class="htmx-indicator"><svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-opacity-10 bg-green-100 text-green-800">● IA</span>
            </div>
        </div>"""

        html_respuesta_oob = f'<div id="contenedor-mensajes-lista" hx-swap-oob="beforeend"><div class="flex flex-col items-end"><div class="max-w-md px-4 py-2 rounded-lg shadow-sm text-sm bg-blue-600 text-white rounded-br-none">{respuesta_final}</div><span class="text-xxs text-gray-400 mt-1 px-1">Rol: bot</span></div></div>'

        await manager.broadcast(html_sidebar_final, channel="global")
        await manager.broadcast(html_respuesta_oob, channel=f"chat_{usuario_id}")
        if accion == "enviar_mapa":
            await http_client.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendLocation", json={"chat_id": chat_id_int, "latitude": 21.0136630685485, "longitude": -89.55584020754324})

    except Exception as e:
        print(f"🔥 [WEBHOOK] ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
    
    return {"status": "ok"}
