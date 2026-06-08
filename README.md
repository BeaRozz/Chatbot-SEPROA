# SEPROA Command Center 🤖💼

Un ecosistema inteligente y multi-agente diseñado para **SEPROA** (Servicio Profesional de Asesores), que integra un Asistente Virtual en Telegram con un Panel Administrativo de alto rendimiento. El sistema automatiza el agendamiento de citas contables y fiscales mediante Inteligencia Artificial y sincronización en tiempo real.

Proyecto final desarrollado por el equipo **Ordinario Agentes** para la materia **Programación de Agentes** en la **Universidad Modelo**, Campus Mérida.

---

## 🔥 Estado del Proyecto: Versión Final Optimizada
El sistema ha evolucionado hacia una arquitectura de alta disponibilidad, eliminando bloqueos de concurrencia y ofreciendo una experiencia de usuario (UX) de nivel profesional.

### Funcionalidades Clave:
*   **Cerebro Multimodal (IA):** Integración con OpenAI `gpt-4o-mini` mediante *Function Calling* para extracción precisa de fechas, servicios y correos electrónicos.
*   **Command Center Administrativo:** Panel web moderno construido con HTMX y Tailwind CSS. Permite monitoreo en tiempo real, intervención manual inmediata y configuración dinámica del bot.
*   **Agenda Inteligente:** Sincronización bidireccional con **Google Calendar API**. El bot valida disponibilidad real y crea eventos automáticamente.
*   **Arquitectura No Bloqueante:** Implementación de hilos secundarios (`asyncio.to_thread`) y optimización de SQLite (WAL Mode) para soportar múltiples usuarios simultáneos sin retardos.
*   **Sistema de Notificaciones:** Recordatorios automáticos vía Telegram y Email gestionados por un Scheduler en segundo plano.

---

## 🛠️ Stack Tecnológico
- **Backend:** FastAPI (Python 3.13)
- **IA:** OpenAI API (GPT-4o-mini)
- **Agenda:** Google Calendar API v3
- **Base de Datos:** SQLite (Modo WAL + Pragmas de alto rendimiento)
- **Frontend:** HTMX, Tailwind CSS, Marked.js (Markdown Rendering)
- **Comunicaciones:** Telegram Bot API, SMTP (Email)

---

## 📂 Documentación Detallada
Para una comprensión profunda del sistema, consulte los manuales en la carpeta `docs/`:

1.  [**Manual de Arquitectura Técnica**](./docs/tecnico_detallado.md): Diagramas Mermaid, flujos de datos y optimizaciones de bajo nivel.
2.  [**Guía del Administrador**](./docs/manual_usuario_final.md): Manual operativo paso a paso con capturas de pantalla para la gestión de clientes.
3.  [**Lógica de Negocio y Reglas**](./docs/logica.md): Diccionario de validaciones de IA, horarios y agendamiento.
4.  [**Limitaciones y Restricciones**](./docs/limitaciones_y_restricciones.md): Análisis de riesgos y alcance técnico.

---

## ⚙️ Instalación y Ejecución Rápida

1.  **Entorno:**
    ```bash
    git clone https://github.com/BeaRozz/Chatbot-SEPROA.git
    cd seproa_bot
    python -m venv venv
    source venv/bin/activate  # o .\venv\Scripts\activate en Windows
    pip install -r requirements.txt
    ```

2.  **Configuración:**
    Cree un archivo `.env` en la raíz con las llaves de API necesarias (Telegram, OpenAI, Google).

3.  **Arranque:**
    ```bash
    uvicorn main:app --reload
    ```
    - **Panel Admin:** `http://localhost:8000/admin/`
    - **API Status:** `http://localhost:8000/`

---
*© 2026 Ordinario Agentes - Universidad Modelo.*
