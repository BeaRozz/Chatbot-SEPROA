# Guía del Administrador - SEPROA Command Center

Bienvenido al centro de mando de tu asistente virtual. Este manual te ayudará a gestionar la atención al cliente y la configuración del bot de forma efectiva.

## 1. Acceso al Panel
El panel administrativo es accesible vía web en:
`http://localhost:8000/admin/`

## 2. Gestión de Conversaciones
Desde el menú lateral de **Conversaciones**, puedes supervisar todos los chats en tiempo real.

### A. Estados de los Usuarios
En la lista de la izquierda verás etiquetas de colores:
- **● IA (Verde):** El bot está respondiendo automáticamente.
- **● Humano (Rojo):** Tú tienes el control total del chat. El bot está pausado.

### B. Intervención Manual (Toma de Control)
Para evitar que el bot y tú escriban al mismo tiempo, hemos implementado un sistema de seguridad:
1. Haz clic en el botón central **"Intervenir y Escribir Manualmente"**.
2. El teclado aparecerá y el bot dejará de procesar respuestas para ese usuario.
3. Cuando termines la gestión manual, pulsa **"Regresar el control a la IA"** para reactivar el asistente.

## 3. Panel de Configuración
Desde aquí personalizas la "mente" de tu bot.

### A. Identidad y Tono
- **Tono de voz:** Puedes cambiar la personalidad del bot (Formal, Empático, Vendedor). Al seleccionarlo, verás una directriz de cómo se comportará la IA.
- **Emojis:** Activa o desactiva el uso de emojis en las respuestas corporativas.
- **Mensajes de Saludo/Despedida:** Son los textos base que el bot usará al iniciar o terminar contacto.

### B. Modo Vacaciones 🏖️
Si la empresa cerrará por un periodo, activa este interruptor:
1. Selecciona la **Fecha de Regreso**.
2. El bot informará automáticamente a todos los clientes que están de descanso y cuándo regresan.
3. **Apagado Automático:** El bot se reactivará solo en cuanto pase la fecha seleccionada.

### C. Catálogo de Servicios y FAQs
- **Servicios:** Añade los nombres y descripciones de tus asesorías. La IA usará esta info para agendar citas.
- **FAQs:** Registra preguntas comunes y sus respuestas. Esto entrena al bot para responder dudas frecuentes sin tu intervención.

### D. Horarios de Atención
- Puedes registrar múltiples bloques horarios por día (ej. Mañana y Tarde).
- El bot solo permitirá agendar citas que caigan dentro de estos rangos laborales.

## 4. Agenda de Citas (Calendario)
Integrado directamente en el panel de configuración, puedes ver el calendario de Google vinculado. Aquí aparecerán instantáneamente las citas que el bot confirme con los clientes.
