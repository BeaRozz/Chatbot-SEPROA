# Limitaciones y Restricciones - Chatbot SEPROA

Este documento detalla las capacidades no soportadas, restricciones lógicas y puntos de falla potenciales identificados en la versión actual del sistema.

## 1. Restricciones de Agendamiento
El motor de IA y el orquestador imponen reglas estrictas que pueden ser percibidas como limitaciones por el usuario final:
- **Citas en Punto:** El sistema **no permite** agendar citas con minutos fraccionados (ej. 10:30 AM). Solo se aceptan horas completas (ej. 10:00 AM).
- **Margen de 2 Horas:** No se permiten citas "urgentes". El usuario debe agendar con al menos **120 minutos de anticipación** respecto a la hora actual del servidor.
- **Duración Fija:** El sistema asume que **todas las citas duran exactamente 1 hora**. No es posible agendar asesorías de 30 minutos o de 2 horas en un solo bloque.
- **Cierre de Oficina:** No se puede agendar una cita a la misma hora de cierre. La última cita permitida es **una hora antes** del fin de jornada.

## 2. Limitaciones de Concurrencia y Hardware
- **Sensibilidad al Disco Duro (I/O):** En equipos con discos mecánicos (HDD), el sistema puede experimentar retrasos si el archivo de base de datos crece demasiado o si hay un alto volumen de lecturas simultáneas del panel. Se recomienda encarecidamente el uso de **SSD**.
- **Bloqueo de SQLite:** Aunque se utiliza el modo WAL, SQLite solo permite un escritor a la vez. Ráfagas extremas de mensajes (ej. 10 mensajes por segundo) podrían causar errores temporales de "Database is locked".
- **Pool de Hilos:** El panel administrativo corre en un pool de hilos limitado. Si se abren demasiadas pestañas de administración simultáneamente, el tiempo de respuesta del panel se degradará.

## 3. Dependencias Externas (Puntos de Falla)
El bot depende de tres servicios externos; si alguno falla, la funcionalidad se verá comprometida:
- **OpenAI API:** Si la API de OpenAI está caída o excede su cuota, el bot no podrá procesar intenciones y dará una respuesta de error técnica.
- **Google Calendar:** La validación de disponibilidad requiere conexión constante con Google. Sin ella, el bot no puede confirmar si un horario está libre.
- **Telegram Bot API:** El bot tiene un límite de **20-30 segundos** para responder. Si la IA tarda más de ese tiempo, Telegram reintentará el mensaje, lo que puede causar duplicidad en las respuestas.

## 4. Limitaciones del Panel Administrativo
- **WebSockets en Túneles:** El uso de herramientas de túnel (como devtunnels.ms o ngrok) puede bloquear la conexión persistente del WebSocket. En estos casos, el sistema recurre al **Polling**, lo que introduce un retraso de hasta 5 segundos para ver mensajes nuevos.
- **Renderizado de Markdown:** La conversión de texto a Markdown ocurre en el navegador del cliente. Dispositivos muy antiguos o navegadores desactualizados podrían mostrar el texto plano sin formato.

## 5. Inteligencia Artificial (Alucinaciones)
- Aunque se han implementado prompts estrictos, el modelo GPT-4o-mini podría, en casos de mensajes muy ambiguos, interpretar erróneamente un día de la semana si el historial de la conversación es contradictorio.
- El bot no tiene memoria de largo plazo más allá de los **últimos 4 mensajes** para optimizar costos y velocidad. Consultas sobre temas tratados mucho antes en la charla serán ignoradas.
