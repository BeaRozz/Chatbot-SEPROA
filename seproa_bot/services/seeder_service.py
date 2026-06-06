from sqlalchemy.orm import Session
from db.models import ConfiguracionBot, Tono, Servicio, PreguntaFrecuente, HorarioAtencion
from datetime import time

def precargar_datos(db: Session):
    # 1. Precargar Tonos
    if db.query(Tono).count() == 0:
        db.add_all([
            Tono(etiqueta="Formal", descripcion="Lenguaje corporativo, respetuoso, usa 'usted' y estructura clara."),
            Tono(etiqueta="Empático", descripcion="Lenguaje cálido, cercano, enfocado en escuchar al usuario."),
            Tono(etiqueta="Vendedor", descripcion="Lenguaje entusiasta, enfocado en resaltar beneficios y agendar citas.")
        ])
        db.commit()

    # 2. Precargar Servicios Básicos
    if db.query(Servicio).count() == 0:
        db.add_all([
            Servicio(nombre="Consultoría Fiscal", descripcion="Análisis y planificación para optimizar impuestos, revisión del cumplimiento de obligaciones fiscales, estrategias para deducciones y beneficios fiscales, atención derequerimientos del SAT y asesoría sobre regímenes fiscales."),
            Servicio(nombre="Consultoría Contable", descripcion="Incluye asesoría en el manejo y organización de la contabilidad, revisión de estados financieros, cumplimiento de normativas contables, optimización de procesos contables y apoyo en la toma de decisiones financieras."),
            Servicio(nombre="Asesoría Administrativa", descripcion="Incluye la optimización de procesos internos, gestión eficiente de recursos, mejora en la toma de decisiones, implementación de estrategias organizacionales y apoyo en la planificación y control administrativo."),
            Servicio(nombre="Servicio de Defensa Fiscal", descripcion="Incluye la representación y asesoría en procedimientos fiscales, atención de auditorías y revisiones del SAT, interposición de recursos de defensa, gestión de amparos y estrategias legales para la protección de los derechos del contribuyente.")
        ])
        db.commit()

    # 3. Precargar FAQs Básicas
    if db.query(PreguntaFrecuente).count() == 0:
        db.add_all([
            PreguntaFrecuente(pregunta="¿Pueden las personas físicas utilizar su E-FIRMA para la emisión y cancelación de CFDI?", respuesta="Sí, las personas físicas pueden utilizar su certificado de E-FIRMA en sustitución del Certificado de Sello Digital para emitir, cancelar o aceptar cancelaciones de comprobantes fiscales."),
            PreguntaFrecuente(pregunta="¿Quiénes pueden renovar su E-FIRMA con E-FIRMA portátil?", respuesta="Las personas físicas que posean un certificado de E-FIRMA portátil pueden renovarlo a través del SAT, incluso si se encuentra activo, caduco o revocado a solicitud del contribuyente."),
            PreguntaFrecuente(pregunta="¿Qué significados puede tener la opinión de cumplimiento de obligaciones fiscales y cuál es su vigencia?", respuesta="La opinión de cumplimiento puede ser Positiva, Negativa o En suspensión de actividades. Una opinión positiva tendrá una vigencia de treinta días naturales a partir de su fecha de emisión. La autoridad verificará diversos puntos para emitir esta opinión, incluyendo avisos al RFC, declaraciones de los últimos 4 años, inconsistencias entre lo declarado y los CFDI, no estar en listados específicos, no tener créditos fiscales firmes, y estar localizado, entre otros."),
            PreguntaFrecuente(pregunta="¿Cuáles son los requisitos para la devolución automática de saldo a favor de ISR para personas físicas?", respuesta="Para la devolución automática, las declaraciones deben presentarse con e-firma o e-firma portable para saldos a favor de $10,001.00 a $150,000.00. Saldos a favor menores a $10,000.00 pueden presentarse con contraseña. También aplica para saldos de $10,000.00 a $150,000.00 si se selecciona una CLABE activa precargada a nombre del contribuyente como titular."),
            PreguntaFrecuente(pregunta="¿En qué casos no aplica la devolución automática de saldo a favor de ISR para personas físicas?", respuesta="La devolución automática no aplica para personas físicas con ingresos en copropiedad, sociedad conyugal o sucesión, montos superiores a $150,000.00, ejercicios distintos al inmediato anterior, o si se presenta con contraseña estando obligado a usar e.firma. Tampoco aplica si se realiza el trámite de devolución vía FED antes de obtener el resultado, si no se elige la opción de devolución (aunque se puede cambiar hasta el 31 de julio), o si se presenta después del 31 de julio. Además, no aplica si el contribuyente está enlistado, incluye deducciones de contribuyentes enlistados, o si le han cancelado el certificado."),
            PreguntaFrecuente(pregunta= "¿Qué tipos de ingresos no se consideran para efectos fiscales?", respuesta="No se consideran ingresos fiscales la venta de casa habitación, donativos exentos, herencias, indemnizaciones salariales, adquisición por prescripción, premios, intereses moratorios, y retiros de afores o planes para el retiro.")
        ])
        db.commit()
    
    if db.query(ConfiguracionBot).count() == 0:
        primer_tono = db.query(Tono).first()
        db.add(ConfiguracionBot(
            tono_id=primer_tono.id if primer_tono else None,
            usa_emojis=True,
            mensaje_saludo="¡Hola! Bienvenido al asistente virtual de SEPROA (Servicio Profesional de Asesores). ¿En qué podemos ayudarte hoy?",
            mensaje_despedida="¡Gracias por ponerte en contacto con SEPROA! Que tengas un excelente día.",
            correo_contacto="seproa@outlook.com",
            telefono_contacto="9991014193",
            ubicacion_contacto="Calle 65a No. 264, Residencial Floresta, Mérida, Yucatán, CP 97302"
        ))
        db.commit()

    if db.query(HorarioAtencion).count() == 0:
        dias_laborales = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        horarios_iniciales = []
        
        for dia in dias_laborales:
            horarios_iniciales.append(
                HorarioAtencion(
                    dia_semana=dia,
                    hora_inicio=time(9, 0),   # 09:00 AM
                    hora_fin=time(15, 0),     # 03:00 PM (15:00)
                    es_laboral=True
                )
            )
                
        db.add_all(horarios_iniciales)
        db.commit()
    