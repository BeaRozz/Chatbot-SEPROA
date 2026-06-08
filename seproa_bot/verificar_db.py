from db.database import SessionLocal
from db.models import Usuario, Mensaje, Cita

def verificar_datos():
    db = SessionLocal()
    try:
        num_usuarios = db.query(Usuario).count()
        num_mensajes = db.query(Mensaje).count()
        num_citas = db.query(Cita).count()
        
        print(f"\n📊 --- REPORTE DE INTEGRIDAD DE DATOS ---")
        print(f"👥 Usuarios registrados: {num_usuarios}")
        print(f"💬 Mensajes guardados: {num_mensajes}")
        print(f"📅 Citas agendadas: {num_citas}")
        
        if num_citas > 0:
            print("\n📌 Últimas 3 citas:")
            ultimas_citas = db.query(Cita).order_by(Cita.id.desc()).limit(3).all()
            for c in ultimas_citas:
                print(f"  - ID: {c.id} | Servicio: {c.tipo_servicio} | Fecha: {c.fecha_hora} | Estado: {c.estado}")
        
        if num_usuarios > 0:
            print("\n👤 Últimos 3 usuarios:")
            ultimos_usuarios = db.query(Usuario).order_by(Usuario.id.desc()).limit(3).all()
            for u in ultimos_usuarios:
                print(f"  - ID: {u.id} | Telegram ID: {u.telegram_id} | Intervenido: {u.esta_intervenido}")

    except Exception as e:
        print(f"❌ Error al consultar la BD: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verificar_datos()
