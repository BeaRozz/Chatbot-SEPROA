# SEPROA Chatbot Empresarial 🤖💼

Un Asistente Virtual Automatizado y Multi-Agente que opera en Telegram para la empresa **SEPROA** (Servicio Profesional de Asesores). El sistema integra un modelo de lenguaje de última generación (LLM) con una base de datos relacional y un panel administrativo web dinámico, permitiendo gestionar la identidad corporativa y la persistencia de interacciones en tiempo real.

Proyecto final desarrollado por el equipo **Ordinario Agentes** para la materia **Programación de Agentes** en la **Universidad Modelo**, Campus Mérida.

---

## 🚀 Estado del Proyecto: Fases 1, 2 y 3 Completadas
El sistema ha evolucionado de un esqueleto base a una arquitectura monolítica modular robusta y optimizada contra la concurrencia y la latencia asíncrona.

### Funcionalidades Actuales:
* **Cerebro conversacional (IA):** Integración asíncrona completa con la API de OpenAI (`gpt-4o-mini`) con inyección de contextos corporativos y memoria histórica.
* **Robustez contra Prompt Injection:** Blindaje lógico mediante ingeniería de prompts avanzada (*Negative Prompting*) para impedir que los usuarios fuercen cambios de tono o simulen ejecuciones técnicas destructivas (ej. "borrar cuenta").
* **Mecanismo de Caché Global en RAM:** El prompt del sistema se compila y almacena en la memoria RAM del servidor de FastAPI durante el arranque (`main.py`) y tras modificaciones del administrador desde el frontend. El bot lee las instrucciones al instante sin saturar SQLite con consultas redundantes por cada mensaje recibido.
* **Optimización FinOps (Costos de API):** Estructura orientada a *Prompt Caching* de OpenAI. Al inyectar el bloque de instrucciones `system` de forma estática e idéntica al inicio del hito, OpenAI aplica de manera automática un **50% de descuento** en los tokens de entrada de la cuenta pagada.
* **Concurrencia Blindada:** Base de datos SQLite indexada en su columna relacional crítica (`telegram_id`) y configurada con un aislamiento de transacciones de tiempo de espera (`timeout=30`), soportando múltiples usuarios platicando en paralelo sin generar bloqueos de disco (*Database is locked*).
* **Panel Administrativo Web:** Interfaz funcional bajo arquitectura Jinja2 para modificar de manera dinámica el tono de voz de la IA, mensajes institucionales de saludo/despedida, activación de estados de vacaciones corporativas y catálogos dinámicos (Servicios, Horarios, FAQs).

---

## 🛠️ Stack Tecnológico
* **Backend & API Framework:** FastAPI (Asíncrono, Python 3)
* **Inteligencia Artificial:** OpenAI API (`gpt-4o-mini`) vía Cliente Asíncrono oficial
* **Base de Datos Local:** SQLite con indexación estructural
* **ORM:** SQLAlchemy (Patrón *Session-per-Request* con ciclos de vida cerrados explícitamente)
* **Peticiones HTTP externas:** HTTPX (Pool de conexiones global reutilizable)
* **Motor de Plantillas:** Jinja2 (Para renderizado del Front-end administrativo)
* **Seguridad:** Python-dotenv (Segregación de credenciales sensibles)

---

## 📁 Estructura del Proyecto

Resultado de código
File README.md successfully created.

```text
seproa_bot/
│
├── main.py                 # Orquestador de arranque, sembrado de caché RAM y FastAPI
├── requirements.txt        # Dependencias del entorno de ejecución
├── .env                    # Credenciales y llaves privadas (¡Ignorado en Git!)
├── .gitignore              # Archivos protegidos del control de versiones
│
├── bot/                     
│   └── telegram_bot.py     # Webhook de Telegram y pool de red HTTPX global (Estable y síncrono por transacción)
│
├── db/                     
│   ├── database.py         # Configuración del Engine con connect_args de concurrencia (timeout=30)
│   └── models.py           # Estructura e índices relacionales (Usuario, Mensaje con index=True, Config)
│
├── web/
│   └── panel_router.py     # Controlador del Panel Web y disparador reactivo de Caché RAM
│
├── services/              
│   ├── openai_service.py   # System Prompt estático, Prompt Caching FinOps y llamadas LLM (max_tokens=120)
│   ├── seeder_service.py   # Precarga autónoma de datos iniciales en SQLite
│   └── cruds/              # Controladores internos para Horarios, Servicios y FAQs
│
├── templates/              # Vistas HTML renderizadas por el servidor para el administrador
└── static/                 # Hojas de estilo (CSS) y recursos del Panel Web
```

---

# ⚙️ Instalación y Configuración Local

Sigue estos pasos para levantar el proyecto de forma segura en tu máquina:

1. Clonar el repositorio y crear el entorno virtual

```bash
git clone https://github.com/BeaRozz/Chatbot-SEPROA.git
cd seproa_bot
python -m venv venv
```

2. Activar el entorno virtual
    * En Windows: `.\\venv\\Scripts\\activate`
    * En Mac/Linux: `source venv/bin/activate`

3. Instalar dependencias
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno
Crea un archivo llamado `.env` en la raíz del proyecto y agrega tus tokens comerciales:
```plaintext
TELEGRAM_TOKEN="TU_TOKEN_DE_TELEGRAM_AQUI"
OPENAI_API_KEY="TU_LLAVE_PAGADA_DE_OPENAI_AQUI"
```

5. Levantar el servidor local
```bash
uvicorn main:app --reload
```
* El backend y el webhook se ejecutarán localmente en http://127.0.0.1:8000.
* El Panel de Administración Web estará disponible en http://127.0.0.1:8000/admin/config.