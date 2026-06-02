# services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

# Pon esto en tu archivo .env o escríbelo aquí directo para probar:
EMAIL_SEPROA = "asucamedina@gmail.com" 
PASSWORD_SEPROA = "iyhy aigz jzxp xquu"

def _enviar_correo_sync(destinatario: str, fecha: str, hora: str, servicio: str):
    asunto = f"Confirmación de Cita SEPROA: Asesoría {servicio}"
    
    cuerpo_html = f"""
    <html>
        <body>
            <h2 style="color: #2c3e50;">¡Tu cita está confirmada!</h2>
            <p>Hola,</p>
            <p>Tu <strong>Asesoría {servicio}</strong> ha sido agendada exitosamente en nuestro sistema.</p>
            <ul>
                <li>📅 <strong>Fecha:</strong> {fecha}</li>
                <li>⏰ <strong>Hora:</strong> {hora}</li>
            </ul>
            <p>Nos vemos pronto en las oficinas de SEPROA.</p>
        </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = f"Asistente SEPROA <{EMAIL_SEPROA}>"
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo_html, 'html'))
    
    try:
        # Conexión al servidor de Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SEPROA, PASSWORD_SEPROA)
        server.send_message(msg)
        server.quit()
        print(f"📧 Correo de confirmación enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

async def enviar_correo_confirmacion(destinatario: str, fecha: str, hora: str, servicio: str):
    """Wrapper asíncrono para enviar correos sin bloquear FastAPI"""
    await asyncio.to_thread(_enviar_correo_sync, destinatario, fecha, hora, servicio)