from sqlalchemy.orm import Session
from db.models import PreguntaFrecuente

def obtener_todas(db: Session):
    """Obtiene todas las preguntas frecuentes registradas."""
    return db.query(PreguntaFrecuente).all()

def agregar(db: Session, pregunta: str, respuesta: str):
    """Valida y guarda una nueva FAQ."""
    # Validación básica de contenido
    if not pregunta or not respuesta or not pregunta.strip() or not respuesta.strip():
        return False, "La pregunta y respuesta no pueden estar vacías."
    
    try:
        nuevo = PreguntaFrecuente(pregunta=pregunta.strip(), respuesta=respuesta.strip())
        db.add(nuevo)
        db.commit()
        return True, "FAQ guardada con éxito."
    except Exception as e:
        db.rollback()
        return False, str(e)

def eliminar(db: Session, faq_id: int):
    """Elimina una FAQ garantizando que el bot siempre tenga al menos una."""
    try:
        if db.query(PreguntaFrecuente).count() > 1:
            faq = db.query(PreguntaFrecuente).filter(PreguntaFrecuente.id == faq_id).first()
            if faq:
                db.delete(faq)
                db.commit()
                return True, "FAQ eliminada."
        else:
            return False, "Debe existir al menos una FAQ."
        return False, "FAQ no encontrada."
    except Exception as e:
        db.rollback()
        return False, str(e)