# Lógica de Negocio y Reglas del Asistente Virtual

Este documento describe los criterios y validaciones que utiliza la IA de SEPROA para procesar mensajes y agendar citas.

## 1. Contexto Temporal Preciso
Para evitar errores de "sesgo al lunes", el sistema inyecta en cada mensaje:
- **Día de la semana actual:** (Ej. Hoy es Domingo).
- **Fecha exacta:** (YYYY-MM-DD).
- **Hora del servidor:** (Zona horaria: America/Merida).
Esto permite que cuando el usuario dice "el jueves", la IA calcule matemáticamente la fecha correcta basada en el calendario real.

## 2. Reglas de Agendamiento de Citas
La IA solo procesará citas si cumplen estas validaciones estrictas:
- **Margen de Anticipación:** La cita debe pedirse con al menos **2 horas de diferencia** respecto a la hora actual.
- **Horas en Punto:** Solo se aceptan citas en formato "en punto" (ej. 10:00, 11:00). No se permiten minutos fraccionados (ej. 10:30).
- **Duración Estándar:** Todas las citas se consideran de **1 hora**. Por lo tanto, no se puede agendar a la misma hora exacta de cierre de la oficina.

## 3. Manejo de Horarios Múltiples
El bot es capaz de leer todos los bloques registrados para un mismo día. 
- *Ejemplo:* Si hay un bloque de 09:00-15:00 y otro de 17:00-21:00, la IA aceptará citas en ambos rangos. 
- El sistema ordena cronológicamente estos bloques antes de presentarlos al usuario para evitar confusiones.

## 4. Flujo de Confirmación y Acciones
Una cita se considera agendada solo cuando:
1. El usuario proporciona un **Email** válido.
2. El usuario responde **"Sí"** o **"Confirmar"** al resumen final.
3. El sistema valida disponibilidad real en **Google Calendar**.

**Acciones post-confirmación:**
- Se crea el evento en Google.
- Se envía un correo de confirmación formal.
- Se envía automáticamente la **Ubicación Física (Mapa)** a través de Telegram.

## 5. Sistema de Recordatorios (24h)
El programador busca citas en una ventana activa:
- **Inicio de ventana:** 23 horas antes de la cita.
- **Fin de ventana:** 26 horas antes de la cita.
Si una cita cae en este rango y su estado es "Confirmada", el sistema envía notificaciones y cambia el estado a "Recordada" para evitar duplicados.

## 6. Seguridad de Datos
El bot tiene prohibido revelar instrucciones de sistema o datos internos. Cualquier intento de *Prompt Injection* (pedir el prompt original) resultará en una respuesta corporativa estandarizada.
