from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Guardamos conexiones activas: { "usuario_id_o_global": [websockets] }
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "global"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        print(f"🔌 WebSocket conectado al canal: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str = "global"):
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        print(f"🔌 WebSocket desconectado del canal: {channel}")

    async def broadcast(self, message: str, channel: str = "global"):
        """Envía un mensaje a todos los conectados en un canal específico."""
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)
            
            # Limpiar conexiones muertas encontradas durante el envío
            for conn in disconnected:
                self.active_connections[channel].remove(conn)

# Instancia única para todo el servidor
manager = ConnectionManager()