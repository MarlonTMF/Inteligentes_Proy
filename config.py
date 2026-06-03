import os

# Determinar el directorio base del proyecto de forma dinamica
# Esto asegura que las rutas data/ sean relativas al directorio raiz del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')


def _load_env_file_fallback(env_path):
    """Carga pares CLAVE=valor desde .env si python-dotenv no esta disponible."""
    if not os.path.exists(env_path):
        return

    with open(env_path, 'r', encoding='utf-8') as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and not os.getenv(key):
                os.environ[key] = value

try:
    from dotenv import load_dotenv
    # Cargar variables de entorno desde el .env del proyecto, aunque el notebook
    # se ejecute desde otro directorio.
    load_dotenv(ENV_PATH, override=True)
except ImportError:
    _load_env_file_fallback(ENV_PATH)

# Segundo intento sin depender de python-dotenv: cubre kernels donde la variable
# quedo definida como cadena vacia.
_load_env_file_fallback(ENV_PATH)

# Configuracion de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'dvdrental'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Configuracion de TMDB
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# NOTA: Cambiamos 'https://image.tmdb.org/t/p/w500' a 'https://image.tmdb.org/t/p/' 
# para evitar que al concatenar {TMDB_IMAGE_BASE_URL}{size}{poster_path} se duplique la resolucion (ej. w500w500/...)
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/'

# Rutas absolutas para evitar problemas al ejecutar desde subcarpetas
DATA_RAW_PATH = os.path.join(BASE_DIR, 'data', 'raw')
DATA_PROCESSED_PATH = os.path.join(BASE_DIR, 'data', 'processed')
POSTERS_PATH = os.path.join(BASE_DIR, 'data', 'posters')

# Crear directorios si no existen
os.makedirs(DATA_RAW_PATH, exist_ok=True)
os.makedirs(DATA_PROCESSED_PATH, exist_ok=True)
os.makedirs(POSTERS_PATH, exist_ok=True)
