from sqlalchemy.orm import Session
from db.models import Servicio

def obtener_todos(db: Session):
    """Devuelve la lista de todos los servicios registrados."""
    return db.query(Servicio).all()

def agregar(db: Session, nombre: str, descripcion: str):
    """Agrega un nuevo servicio al catálogo."""
    try:
        nuevo_servicio = Servicio(nombre=nombre, descripcion=descripcion)
        db.add(nuevo_servicio)
        db.commit()
        db.refresh(nuevo_servicio)
        return nuevo_servicio
    except Exception as e:
        db.rollback()
        print(f"Error al agregar servicio: {e}")
        return None

def eliminar(db: Session, servicio_id: int):
    """Elimina un servicio, pero protege el sistema para que siempre haya al menos uno."""
    try:
        # Validación crítica: no permitir que la tabla quede vacía
        if db.query(Servicio).count() <= 1:
            return False 
            
        servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
        if servicio:
            db.delete(servicio)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar servicio: {e}")
        return False