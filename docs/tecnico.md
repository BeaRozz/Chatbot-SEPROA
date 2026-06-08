# Manual de Arquitectura Técnica - SEPROA Chatbot

Este documento detalla la estructura, flujo y optimizaciones del ecosistema Chatbot-SEPROA, diseñado para la gestión automatizada de citas contables y administrativas.

## 1. Pila Tecnológica (Tech Stack)
- **Backend:** Python 3.13 + FastAPI.
- **Base de Datos:** SQLite con modo WAL (Write-Ahead Logging).
- **ORM:** SQLAlchemy (Sincrónico).
- **Inteligencia Artificial:** OpenAI API (Modelo: GPT-4o-mini).
- **Frontend:** HTMX + Tailwind CSS + Jinja2 Templates.
- **Integraciones:** Telegram Bot API, Google Calendar API v3, SMTP.
- **Servidor Web:** Uvicorn.

## 2. Arquitectura de Concurrencia
Para resolver bloqueos en entornos con alta latencia de disco (HDD) y peticiones simultáneas, el sistema implementa:

### A. Hilos de Ejecución (Multithreading)
Las operaciones de base de datos son síncronas por naturaleza en SQLAlchemy. Para no bloquear el **Event Loop** de FastAPI, todas las consultas pesadas y escrituras se ejecutan en hilos secundarios mediante `asyncio.to_thread`.
- **Fase 1 (Registro):** Captura inmediata del mensaje del usuario.
- **Fase 2 (Contexto):** Extracción de historial fuera del hilo principal.
- **Fase 3 (Guardado):** Persistencia de la respuesta de la IA sin detener el servidor.

### B. Optimizaciones de SQLite
Configuración de Pragmas para alta disponibilidad:
- `journal_mode=WAL`: Permite lecturas simultáneas mientras se escribe.
- `synchronous=OFF`: Acelera las transacciones al no esperar confirmación física inmediata del disco.
- `busy_timeout=60000`: Manejo robusto de colisiones de escritura (reintentos de 60s).

## 3. Lógica del Bot (Orquestador)
El "cerebro" del bot (`bot/orquestador.py`) opera como una máquina de estados:
1. **Detección de Seguridad:** Filtra ataques de *Prompt Injection*.
2. **Detección de Intención:** Clasifica si el usuario busca información, ubicación o agendamiento.
3. **Motor de Extracción:** Utiliza *Function Calling* de OpenAI para convertir lenguaje natural en JSON (Fecha, Hora, Servicio).
4. **Validación de Reglas de Negocio:** Verifica horarios laborales, disponibilidad en Google Calendar y margen de 2 horas para citas.

## 4. Panel Administrativo (Command Center)
Diseñado para la intervención humana y configuración dinámica:
- **Navegación HTMX:** Carga de contenidos sin recarga de página.
- **Actualización OOB (Out-of-Band):** Inyección instantánea de mensajes nuevos en la pantalla mediante WebSockets/Polling.
- **Resiliencia Híbrida:** Si el túnel de desarrollo bloquea los WebSockets, el sistema activa automáticamente un **Polling de respaldo** cada 5 segundos.

## 6. Herramientas de Auditoría
Se han incluido scripts en la raíz del proyecto para la supervisión manual:
- `verificar_db.py`: Resumen rápido de integridad (conteo de usuarios, mensajes y citas).
- `reporte_detallado.py`: Reporte completo y formateado de todas las citas y horarios registrados.
