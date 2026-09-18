import sqlite3
import logging

DB_NAME = "ecosistema_privado.db"

def inicializar_base_datos():
    """Crea la base de datos y las tablas principales si no existen."""
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        
        # Tabla para guardar historiales de chat o interacciones privadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conexion.commit()
        conexion.close()
        logging.info("Base de datos privada inicializada y tabla creada con éxito.")
    except Exception as e:
        logging.error(f"Error al crear la base de datos: {e}")

if __name__ == "__main__":
    inicializar_base_datos()
    print("¡Base de datos creada correctamente!")