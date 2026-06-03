try:
    import psycopg2
except ImportError:
    psycopg2 = None
import pandas as pd
import sys
import os

# Agregar el directorio raiz al path de Python para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def run_validation_queries(conn):
    """Ejecuta consultas de integridad y comprueba si los valores estan dentro de los rangos esperados."""
    validations = [
        {'name': 'Cantidad de peliculas', 'query': 'SELECT COUNT(*) FROM film', 'expected_min': 600, 'expected_max': 1200},
        {'name': 'Cantidad de clientes', 'query': 'SELECT COUNT(*) FROM customer', 'expected_min': 500, 'expected_max': 700},
        {'name': 'Cantidad de alquileres', 'query': 'SELECT COUNT(*) FROM rental', 'expected_min': 10000, 'expected_max': 20000},
        {'name': 'Ingreso total', 'query': 'SELECT SUM(amount) FROM payment', 'expected_min': 70000, 'expected_max': 80000},
    ]
    
    print("=== VALIDACIONES DE INTEGRIDAD ===\n")
    for val in validations:
        try:
            df = pd.read_sql(val['query'], conn)
            value = df.iloc[0, 0]
            
            # Formatear el valor segun el tipo para una mejor visualizacion
            if isinstance(value, float):
                val_str = f"{value:.2f}"
            else:
                val_str = str(value)
                
            status = "OK" if (val['expected_min'] <= value <= val['expected_max']) else "FALLO"
            print(f"{val['name']}: {val_str} [{status}]")
            print(f"  Esperado entre {val['expected_min']} y {val['expected_max']}\n")
            
            if status == "FALLO" and val['name'] == 'Ingreso total':
                print("  [Nota de Analisis] El total real de ingresos en la base de datos estandar Sakila/DVD-rental ")
                print(f"  es aproximadamente $67,416.51. Por lo tanto, un rango minimo de $70,000 resultara en FALLO.\n")
                
        except Exception as e:
            print(f"Error al ejecutar la consulta para '{val['name']}': {e}\n")

if __name__ == "__main__":
    conn = None
    if psycopg2 is not None:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print("Conectado a la base de datos PostgreSQL para validacion.")
            run_validation_queries(conn)
        except Exception as e:
            print(f"No se pudo conectar a PostgreSQL para validacion: {e}")
            conn = None
    else:
        print("Libreria 'psycopg2' no instalada. No se puede conectar a la base de datos PostgreSQL.")
        conn = None

    if conn is None:
        print("\n=== SIMULACION DE VALIDACIONES (DEMO LOCAL) ===")
        # Simulacion realista de Sakila para demostrar el comportamiento del codigo
        print("Cantidad de peliculas: 1000 [OK] (Esperado entre 600 y 1200)")
        print("Cantidad de clientes: 599 [OK] (Esperado entre 500 y 700)")
        print("Cantidad de alquileres: 16044 [OK] (Esperado entre 10000 y 20000)")
        print("Ingreso total: 67416.51 [FALLO] (Esperado entre 70000 y 80000)")
        print("  [Nota de Analisis] El total real de ingresos de Sakila es $67,416.51, lo cual es inferior al umbral minimo de $70,000.\n")
        
    if conn:
        conn.close()
