# Manual de Usuario - SEPROA Command Center

Bienvenido al manual de operación del Chatbot SEPROA. Este documento le guiará paso a paso en el uso de las herramientas de monitoreo y configuración.

---

## 1. Acceso al Sistema
Para ingresar al panel administrativo, abra su navegador y diríjase a:
`http://localhost:8000/admin/`

![Pantalla inicial del Dashboard mostrando el Sidebar y el área central](placeholder_dashboard_inicial.png)
*Descripción: Vista general del centro de mando al iniciar sesión.*

---

## 2. Monitoreo de Conversaciones
Esta sección permite supervisar la actividad de los usuarios y el bot en tiempo real.

### 2.1 El Sidebar (Lista de Usuarios)
En el panel izquierdo verá a todos los clientes que han interactuado con el bot.

- **Resaltado Azul:** Indica el chat que está consultando actualmente.
- **Tag IA (Verde):** El asistente virtual está respondiendo.
- **Tag Humano (Rojo):** Usted tiene el control del chat.
- **Previsualización:** Muestra un fragmento del último mensaje enviado/recibido.

![Sidebar de conversaciones con diferentes estados de usuarios](placeholder_sidebar_usuarios.png)
*Descripción: El sidebar permite identificar rápidamente quién necesita atención y quién está siendo atendido por la IA.*

### 2.2 Gestión de Chats e Intervención
Al seleccionar un usuario, se desplegará la conversación. Por seguridad, el teclado está bloqueado mientras la IA está activa.

**Pasos para intervenir:**
1. Visualice el botón central **"Intervenir y Escribir Manualmente"**.
2. Al pulsarlo, se habilitará el campo de texto inferior.
3. Escriba su mensaje y pulse **Enviar**.

![Vista de un chat activo con el asistente virtual al mando](placeholder_chat_ia_activo.png)
*Descripción: Interfaz de chat bloqueada mientras el Asistente IA gestiona la comunicación.*

![Vista de chat intervenido con el teclado habilitado](placeholder_chat_intervenido.png)
*Descripción: Interfaz de chat tras activar el control manual; observe el indicador rojo de "Modo Manual".*

---

## 3. Panel de Configuración
Aquí puede personalizar la identidad y las reglas que rigen al bot.

### 3.1 Identidad y Mensajes Base
Configure el nombre, tono de voz y los mensajes de bienvenida que los usuarios recibirán en Telegram.

![Sección de Configuración General e Identidad](placeholder_config_general.png)
*Descripción: Formulario para cambiar el tono (Formal/Empático), activar emojis y editar saludos.*

### 3.2 Modo Vacaciones 🏖️
Utilice esta función para informar a sus clientes sobre periodos de inactividad.

**Pasos:**
1. Active el interruptor de **Modo Vacaciones**.
2. Seleccione la **Fecha de Regreso** en el calendario.
3. Pulse **Guardar Cambios**. El bot se reactivará solo al llegar la fecha indicada.

![Configuración del Modo Vacaciones activado](placeholder_modo_vacaciones.png)
*Descripción: El bot rechazará agendamientos automáticamente durante este periodo.*

### 3.3 Catálogo de Servicios y FAQs
Defina qué servicios ofrece y qué preguntas comunes puede responder el bot.

![Sección de Servicios y Preguntas Frecuentes](placeholder_servicios_faqs.png)
*Descripción: Listas dinámicas para añadir o eliminar servicios contables y respuestas automáticas.*

### 3.4 Gestión de Horarios
El bot solo permitirá agendar citas en los rangos aquí definidos. Puede añadir múltiples bloques (ej. 9:00 - 14:00 y 16:00 - 20:00).

![Tabla de Horarios de Atención](placeholder_horarios.png)
*Descripción: Control de días laborales y horas de apertura/cierre.*

---

## 4. Integración con Google Calendar
En la pestaña de configuración encontrará el calendario corporativo sincronizado. Las citas que el bot confirma aparecen aquí al instante.

![Iframe de Google Calendar integrado en el panel](placeholder_calendario.png)
*Descripción: Visualización en tiempo real de la agenda de SEPROA.*

---

## 5. Notificaciones de Recordatorio
El sistema enviará automáticamente recordatorios por Telegram y Correo 24 horas antes de cada cita. No requiere acción manual, el proceso se ejecuta en segundo plano cada 30 minutos.
