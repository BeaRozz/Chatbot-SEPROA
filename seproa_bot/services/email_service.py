import os
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import urllib.parse

# Cargar las variables desde el .env
load_dotenv()

# Extraer credenciales seguras
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") 
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def _enviar_correo_sync(email_destino: str, fecha: str, hora: str, servicio: str, ubicacion_empresa: str) -> bool:
    """Función interna síncrona que hace el trabajo pesado de conectarse a Gmail."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("⚠️ Advertencia: No se han configurado SMTP_EMAIL o SMTP_PASSWORD en el archivo .env")
        return False

    try:
        # Construcción del mensaje
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Confirmación de Cita SEPROA - {servicio}"
        msg["From"] = f"SEPROA Asesores <{SMTP_EMAIL}>"
        msg["To"] = email_destino

        # Crear un link de Google Maps dinámico codificando los espacios a formato URL
        ubicacion_url = urllib.parse.quote(ubicacion_empresa)
        link_maps = f"https://maps.google.com/?q={ubicacion_url}"

        # Cuerpo del correo en formato HTML
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                
                <div style="background-color: #0d6efd; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">¡Tu cita está confirmada! ✅</h2>
                </div>
                
                <div style="padding: 25px;">
                    <p style="font-size: 16px;">Hola,</p>
                    <p style="font-size: 16px;">Tu cita para asesoría en <strong>{servicio}</strong> con SEPROA ha sido agendada exitosamente en nuestro sistema.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px 20px; border-left: 5px solid #0d6efd; margin: 25px 0; border-radius: 4px;">
                        <p style="margin: 8px 0; font-size: 16px;">📅 <strong>Fecha:</strong> {fecha}</p>
                        <p style="margin: 8px 0; font-size: 16px;">⏰ <strong>Hora:</strong> {hora}</p>
                        <p style="margin: 8px 0; font-size: 16px;">💼 <strong>Servicio:</strong> {servicio}</p>
                    </div>

                    <h3 style="color: #0d6efd; margin-bottom: 10px;">📍 Ubicación de nuestras oficinas</h3>
                    <p style="font-size: 15px; color: #555;">{ubicacion_empresa}</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{link_maps}" style="display: inline-block; padding: 12px 25px; background-color: #198754; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                           🗺️ Abrir en Google Maps
                        </a>
                    </div>

                    <p style="font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px;">
                        Te sugerimos llegar 5 minutos antes. Si necesitas reprogramar o tienes alguna duda, responde a este correo.
                    </p>
                    <p style="font-size: 16px; margin-bottom: 0;">Atentamente,<br><strong>El Equipo de SEPROA</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

        # Adjuntar HTML al mensaje
        parte_html = MIMEText(html, "html")
        msg.attach(parte_html)

        # Conectarse al servidor y enviar
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Seguridad de encriptación
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, email_destino, msg.as_string())
        server.quit()

        print(f"📧 Correo de confirmación enviado exitosamente a {email_destino}")
        return True

    except Exception as e:
        print(f"❌ Error al enviar el correo a {email_destino}: {e}")
        return False


# Función asíncrona que tu Orquestador mandará a llamar
async def enviar_correo_confirmacion(email_destino: str, fecha: str, hora: str, servicio: str, ubicacion_empresa: str) -> bool:
    """
    Envuelve el proceso de envío de correo en un hilo secundario (to_thread) 
    para evitar que FastAPI y el Webhook de Telegram se queden congelados.
    """
    return await asyncio.to_thread(_enviar_correo_sync, email_destino, fecha, hora, servicio, ubicacion_empresa)