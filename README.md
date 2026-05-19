# SEPROA Chatbot Empresarial 🤖💼

Un Asistente Virtual Automatizado operando en Telegram para la empresa **SEPROA** (Servicio Profesional de Asesores). Este proyecto está diseñado para optimizar la atención al cliente, brindar información sobre servicios (fiscales, contables, administrativos) y, en el futuro, gestionar citas automatizadas.

Desarrollado por el equipo **Ordinario Agentes** como proyecto final para la materia de Programación de Agentes.

---

## 🚀 Estado del Proyecto: Fase 1 Completada
Actualmente, el proyecto se encuentra al final de la **Fase 1: Esqueleto y Hola Mundo**. 

### Funcionalidades actuales:
* Servidor backend asíncrono levantado y funcional.
* Base de datos local configurada con creación automática de tablas.
* Registro automático de usuarios nuevos (mediante su Telegram ID).
* Registro de historial de mensajes (Usuario / Bot).
* Conexión exitosa vía Webhook con la API de Telegram.
* Funcionalidad de "Eco" (el bot responde reflejando el mensaje del usuario).

---

## 🛠️ Stack Tecnológico (Fase 1)
* **Backend:** FastAPI, Python 3
* **Base de Datos:** SQLite
* **ORM:** SQLAlchemy
* **Peticiones HTTP:** httpx (Cliente asíncrono)
* **Seguridad:** python-dotenv (Gestión de variables de entorno)

---

## 📁 Estructura del Proyecto

\`\`\`text
seproa_bot/
│
├── main.py                 # Servidor principal y Webhook de Telegram
├── requirements.txt        # Dependencias del entorno
├── .env                    # Variables de entorno (¡No subir a Git!)
├── .gitignore              # Archivos ignorados por el control de versiones
│
├── bot/                    # Lógica del asistente (En construcción)
├── db/                     
│   ├── database.py         # Configuración del motor SQLite
│   └── models.py           # Modelos SQLAlchemy (Usuario, Mensaje)
│
├── servicios/              # Integraciones externas (OpenAI, Google Calendar)
├── templates/              # Vistas para el Panel Web (Fase 3)
└── static/                 # Recursos estáticos para el Panel Web (Fase 3)
\`\`\`

---

## ⚙️ Instalación y Configuración Local

Sigue estos pasos para levantar el proyecto en un entorno de desarrollo local:

**1. Clonar el repositorio y crear el entorno virtual**
\`\`\`bash
git clone <URL_DEL_REPOSITORIO>
cd seproa_bot
python -m venv venv
\`\`\`

**2. Activar el entorno virtual**
* En Windows: `.\venv\Scripts\activate`
* En Mac/Linux: `source venv/bin/activate`

**3. Instalar dependencias**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

**4. Configurar variables de entorno**
Crea un archivo llamado `.env` en la raíz del proyecto y agrega tu token de Telegram proporcionado por BotFather:
\`\`\`text
TELEGRAM_BOT_TOKEN="TU_TOKEN_AQUI"
\`\`\`

**5. Levantar el servidor local**
\`\`\`bash
uvicorn main:app --reload
\`\`\`
*El servidor estará corriendo en `http://127.0.0.1:8000`.*

**6. Configurar el Webhook (Modo Desarrollo)**
1. Abre un túnel hacia el puerto 8000 (puedes usar la pestaña "Ports" de VS Code o Ngrok).
2. Asegúrate de que la visibilidad del túnel sea **Pública**.
3. Registra el Webhook en Telegram abriendo la siguiente URL en tu navegador:
   \`https://api.telegram.org/bot<TU_TOKEN>/setWebhook?url=<TU_URL_PUBLICA>/webhook\`
