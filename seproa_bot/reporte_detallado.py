from db.database import SessionLocal
from db.models import Cita, HorarioAtencion

def reporte_detallado():
    db = SessionLocal()
    try:
        print("\n📅 --- REPORTE COMPLETO DE CITAS AGENDADAS ---")
        citas = db.query(Cita).order_by(Cita.fecha_hora).all()
        if not citas:
            print("No hay citas registradas.")
        else:
            print(f"{'ID':<4} | {'Servicio':<25} | {'Fecha y Hora':<20} | {'Estado':<15} | {'Email'}")
            print("-" * 90)
            for c in citas:
                email = c.email_usuario if c.email_usuario else "N/A"
                print(f"{c.id:<4} | {c.tipo_servicio:<25} | {str(c.fecha_hora):<20} | {c.estado:<15} | {email}")

        print("\n⏰ --- CONFIGURACIÓN DE HORARIOS DE ATENCIÓN ---")
        orden_dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
        horarios = db.query(HorarioAtencion).all()
        horarios_ordenados = sorted(horarios, key=lambda x: (orden_dias.get(x.dia_semana, 99), x.hora_inicio))
        
        if not horarios:
            print("No hay horarios configurados.")
        else:
            print(f"{'Día':<12} | {'Apertura':<10} | {'Cierre':<10} | {'Estado'}")
            print("-" * 50)
            for h in horarios_ordenados:
                estado = "Laboral" if h.es_laboral else "Cerrado"
                inicio = h.hora_inicio.strftime('%H:%M') if h.hora_inicio else "--:--"
                fin = h.hora_fin.strftime('%H:%M') if h.hora_fin else "--:--"
                print(f"{h.dia_semana:<12} | {inicio:<10} | {fin:<10} | {estado}")

    except Exception as e:
        print(f"❌ Error al consultar la BD: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reporte_detallado()
