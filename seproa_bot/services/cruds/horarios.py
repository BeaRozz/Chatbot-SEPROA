from sqlalchemy.orm import Session
from datetime import datetime
from db.models import HorarioAtencion

def obtener_todos(db: Session):
    return db.query(HorarioAtencion).order_by(HorarioAtencion.dia_semana).all()

def agregar(db: Session, dia: str, inicio_str: str, fin_str: str):
    """
    Agrega un horario validando que no se encime con otros el mismo día.
    """
    try:
        h_inicio = datetime.strptime(inicio_str, "%H:%M").time()
        h_fin = datetime.strptime(fin_str, "%H:%M").time()

        if h_inicio >= h_fin:
            return False, "La hora de inicio debe ser anterior a la de fin."

        # Validar superposición
        existentes = db.query(HorarioAtencion).filter(HorarioAtencion.dia_semana == dia).all()
        for h in existentes:
            # Lógica de solapamiento: (InicioA < FinB) y (FinA > InicioB)
            if not (h_fin <= h.hora_inicio or h_inicio >= h.hora_fin):
                return False, f"El horario se encima con uno existente ({h.hora_inicio} - {h.hora_fin})."

        db.add(HorarioAtencion(dia_semana=dia, hora_inicio=h_inicio, hora_fin=h_fin))
        db.commit()
        return True, "Horario guardado correctamente."
    except Exception as e:
        db.rollback()
        return False, str(e)

def eliminar(db: Session, horario_id: int):
    try:
        # Mínimo 1 horario laboral total
        if db.query(HorarioAtencion).count() > 1:
            h = db.query(HorarioAtencion).filter(HorarioAtencion.id == horario_id).first()
            if h:
                db.delete(h)
                db.commit()
                return True
        return False
    except:
        db.rollback()
        return False