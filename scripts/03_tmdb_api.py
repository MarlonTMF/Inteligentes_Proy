import requests
import time
import pandas as pd
import sys
import os

# Agregar el directorio raiz al path de Python para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TMDB_API_KEY, TMDB_BASE_URL

class TMDBClient:
    """Cliente para interactuar con la API de TMDB de manera eficiente y respetando limites."""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = TMDB_BASE_URL
        self.session = requests.Session()
        # Se agregan los parametros por defecto a la sesion
        self.session.params = {
            'api_key': self.api_key,
            'language': 'es-ES'
        }
        self.last_request_time = 0
        self.request_delay = 0.2  # Retardo minimo entre peticiones en segundos (5 peticiones por segundo)

    def _rate_limit(self):
        """Aplica un control de tasa para evitar saturar la API de TMDB."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def search_movie(self, title, year=None):
        """Busca una pelicula por titulo y año opcional."""
        if not self.api_key:
            # Retorno simulado si no hay API key para evitar excepciones fatales en demostraciones
            print("[Warning] TMDB_API_KEY no configurada. Simulando busqueda.")
            return {
                'results': [{
                    'id': 9999,
                    'title': title,
                    'poster_path': '/mock_poster.jpg',
                    'release_date': f"{year}-01-01" if year else "2026-01-01"
                }]
            }
        
        self._rate_limit()
        url = f"{self.base_url}/search/movie"
        params = {'query': title}
        if year:
            params['year'] = year
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[Error API TMDB] Codigo de estado: {response.status_code} para {title}")
                return None
        except Exception as e:
            print(f"[Exception TMDB] Error de conexion: {e}")
            return None

    def get_movie_details(self, movie_id):
        """Obtiene detalles especificos de una pelicula."""
        if not self.api_key:
            return {'id': movie_id, 'title': 'Pelicula Simulada', 'poster_path': '/mock_poster.jpg'}
            
        self._rate_limit()
        url = f"{self.base_url}/movie/{movie_id}"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[Exception TMDB] Error al obtener detalles: {e}")
            return None

    def get_poster_url(self, poster_path, size='w500'):
        """Construye la URL completa del poster. Si es una busqueda simulada, retorna una imagen real de prueba."""
        if not poster_path:
            return None
        if poster_path == '/mock_poster.jpg':
            return 'https://picsum.photos/500/750'
        from config import TMDB_IMAGE_BASE_URL
        return f"{TMDB_IMAGE_BASE_URL}{size}{poster_path}"

def search_film_in_tmdb(client, film_title, release_year=None):
    """Busca una pelicula con multiples fallbacks de busqueda si el titulo exacto de Sakila falla."""
    # 1. Intento exacto de busqueda con titulo y año
    result = client.search_movie(film_title, release_year)
    if result and result.get('results'):
        return result['results'][0]
        
    # 2. Si falla y se especifico año, intentar sin filtro de año
    if release_year:
        result = client.search_movie(film_title)
        if result and result.get('results'):
            return result['results'][0]
            
    # 3. Si falla (comun en titulos dummy de Sakila como 'Academy Dinosaur' o 'Ace Goldfinger'),
    #    intentar buscar usando palabras individuales (por ejemplo, la ultima palabra 'Dinosaur' o 'Goldfinger')
    words = [w for w in film_title.split() if len(w) > 2]
    if len(words) > 1:
        # Intentamos primero con la ultima palabra (suele ser el sustantivo tematico en Sakila)
        for target_word in reversed(words):
            result = client.search_movie(target_word)
            if result and result.get('results'):
                return result['results'][0]
        # Si no, probamos con el primer termino largo
        for target_word in words:
            result = client.search_movie(target_word)
            if result and result.get('results'):
                return result['results'][0]
                
    return None

def get_all_films_from_db(conn):
    """Obtiene todas las peliculas de la base de datos local de PostgreSQL."""
    query = """
    SELECT film_id, title, release_year
    FROM film
    ORDER BY film_id
    """
    df = pd.read_sql(query, conn)
    return df

if __name__ == "__main__":
    print("=== PROBANDO CLIENTE TMDB ===")
    client = TMDBClient(TMDB_API_KEY)
    result = client.search_movie("The Matrix")
    print(f"Resultado de busqueda: {result}")
