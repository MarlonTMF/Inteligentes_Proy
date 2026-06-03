try:
    import psycopg2
except ImportError:
    psycopg2 = None
import pandas as pd
import requests
import time
import os
import argparse
try:
    from tqdm import tqdm
except ImportError:
    # Fallback si tqdm no esta instalado
    def tqdm(iterable, *args, **kwargs):
        return iterable
import sys

# Agregar el directorio raiz al path de Python para importar config y scripts_03_tmdb_api
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)
sys.path.append(SCRIPT_DIR)
from config import DB_CONFIG, POSTERS_PATH, TMDB_API_KEY

# Importamos del modulo intermediario 'scripts_03_tmdb_api' que crearemos
from scripts_03_tmdb_api import TMDBClient, search_film_in_tmdb

def download_image(url, save_path):
    """Descarga una imagen de internet y la guarda en la ruta especificada."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return False

def get_poster_filename(film_id, title):
    """Genera un nombre de archivo seguro y formateado para el poster."""
    safe_title = "".join(
        c if c.isalnum() or c in (" ", "_", "-") else "_" for c in str(title)
    )
    safe_title = "_".join(safe_title.split())
    return f"{film_id:04d}_{safe_title}.jpg"

def get_popular_movies_from_tmdb(limit=150):
    """Importa peliculas populares desde TMDB para tener un dataset local suficiente."""
    client = TMDBClient(TMDB_API_KEY)
    rows = []
    page = 1

    while len(rows) < limit:
        client._rate_limit()
        url = f"{client.base_url}/movie/popular"
        try:
            response = client.session.get(url, params={"page": page}, timeout=15)
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            print(f"[Error] No se pudo importar la pagina {page} de TMDB: {e}")
            break

        results = payload.get("results", [])
        if not results:
            break

        for movie in results:
            if len(rows) >= limit:
                break
            if not movie.get("poster_path"):
                continue
            release_date = movie.get("release_date") or ""
            release_year = int(release_date[:4]) if release_date[:4].isdigit() else None
            rows.append({
                "film_id": len(rows) + 1,
                "title": movie.get("title") or movie.get("original_title") or f"Movie {len(rows) + 1}",
                "release_year": release_year,
                "tmdb_id": movie.get("id"),
                "poster_path": movie.get("poster_path"),
            })

        page += 1
        if page > payload.get("total_pages", page):
            break

    return pd.DataFrame(rows).head(limit)

def download_posters_for_all_films(conn, limit=None):
    """Busca y descarga posters para las peliculas desde la base de datos o fallback."""
    if conn is not None:
        query = "SELECT film_id, title, release_year FROM film ORDER BY film_id"
        try:
            films = pd.read_sql(query, conn)
        except Exception as e:
            print(f"[Error] Fallo al consultar la base de datos: {e}")
            conn = None
            
    if conn is None:
        print("[Warning] No hay conexion activa a PostgreSQL. Usando fallback de peliculas de Sakila/DVD-Rental.")
        # Peliculas representativas de DVD Rental para pruebas
        films = pd.DataFrame([
            {'film_id': 1, 'title': 'Academy Dinosaur', 'release_year': 2006},
            {'film_id': 2, 'title': 'Ace Goldfinger', 'release_year': 2006},
            {'film_id': 3, 'title': 'Adaptation Holes', 'release_year': 2006},
            {'film_id': 4, 'title': 'Affair Prejudice', 'release_year': 2006},
            {'film_id': 5, 'title': 'African Egg', 'release_year': 2006},
            {'film_id': 6, 'title': 'Agent Truman', 'release_year': 2006},
            {'film_id': 7, 'title': 'Airplane Sierra', 'release_year': 2006},
            {'film_id': 8, 'title': 'Airport Pollock', 'release_year': 2006},
            {'film_id': 9, 'title': 'Alabama Devil', 'release_year': 2006},
            {'film_id': 10, 'title': 'Aladdin Calendar', 'release_year': 2006},
        ])

    if limit:
        films = films.head(limit)
        
    print(f"Procesando {len(films)} peliculas...")
    client = TMDBClient(TMDB_API_KEY)
    results = []
    
    for _, row in tqdm(films.iterrows(), total=len(films)):
        film_id = int(row['film_id'])
        title = str(row['title'])
        year = int(row['release_year']) if pd.notnull(row['release_year']) else None
        
        result = {
            'film_id': film_id,
            'title': title,
            'poster_downloaded': False,
            'tmdb_id': None,
            'poster_path': None,
            'filename': None
        }
        
        tmdb_movie = search_film_in_tmdb(client, title, year)
        if tmdb_movie:
            poster_path = tmdb_movie.get('poster_path')
            if poster_path:
                poster_url = client.get_poster_url(poster_path)
                filename = get_poster_filename(film_id, title)
                save_path = os.path.join(POSTERS_PATH, filename)
                
                # Intentar descargar la imagen
                if download_image(poster_url, save_path):
                    result['poster_downloaded'] = True
                    result['tmdb_id'] = tmdb_movie.get('id')
                    result['poster_path'] = poster_path
                    result['filename'] = filename
                    
        results.append(result)
        time.sleep(0.1) # Breve retardo para respetar politicas de TMDB
        
    # Convertir a DataFrame y guardar log de descargas
    results_df = pd.DataFrame(results)
    log_path = os.path.join(POSTERS_PATH, "poster_download_log.csv")
    results_df.to_csv(log_path, index=False)
    
    downloaded = sum(1 for r in results if r['poster_downloaded'])
    print(f"\nResumen: {downloaded}/{len(results)} posters descargados.")
    return results_df

def download_popular_posters(limit=150):
    """Descarga posters de peliculas populares de TMDB y crea un CSV local."""
    films = get_popular_movies_from_tmdb(limit=limit)
    if films.empty:
        raise RuntimeError("No se importaron peliculas desde TMDB. Verifica TMDB_API_KEY o conexion.")

    print(f"Procesando {len(films)} peliculas populares de TMDB...")
    client = TMDBClient(TMDB_API_KEY)
    results = []

    for _, row in tqdm(films.iterrows(), total=len(films)):
        film_id = int(row["film_id"])
        title = str(row["title"])
        poster_path = row["poster_path"]
        filename = get_poster_filename(film_id, title)
        save_path = os.path.join(POSTERS_PATH, filename)

        result = {
            "film_id": film_id,
            "title": title,
            "release_year": row.get("release_year"),
            "poster_downloaded": False,
            "tmdb_id": row.get("tmdb_id"),
            "poster_path": poster_path,
            "filename": filename,
        }

        if os.path.exists(save_path):
            result["poster_downloaded"] = True
        else:
            poster_url = client.get_poster_url(poster_path)
            result["poster_downloaded"] = download_image(poster_url, save_path)
            time.sleep(0.05)

        results.append(result)

    results_df = pd.DataFrame(results)
    log_path = os.path.join(POSTERS_PATH, "poster_download_log.csv")
    results_df.to_csv(log_path, index=False)

    downloaded = int(results_df["poster_downloaded"].sum())
    print(f"\nResumen: {downloaded}/{len(results_df)} posters descargados.")
    print(f"Log guardado en: {log_path}")
    return results_df

def verify_downloaded_posters():
    """Verifica la cantidad de archivos JPG existentes en el directorio de posters."""
    poster_files = os.listdir(POSTERS_PATH)
    jpg_files = [f for f in poster_files if f.endswith('.jpg')]
    print(f"Archivos en carpeta: {len(jpg_files)}")
    return len(jpg_files)

def parse_args():
    parser = argparse.ArgumentParser(description="Importa peliculas y descarga posters.")
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument(
        "--source",
        choices=["tmdb-popular", "db"],
        default="tmdb-popular",
        help="tmdb-popular no requiere PostgreSQL; db usa la tabla film local.",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    conn = None
    if args.source == "db" and psycopg2 is not None:
        try:
            # Intentar conexion a base de datos
            conn = psycopg2.connect(**DB_CONFIG)
            print("Conexion establecida con la base de datos PostgreSQL.")
        except Exception as e:
            print(f"No se pudo conectar a PostgreSQL ({e}). Se continuara en modo local sin base de datos.")
    else:
        if args.source == "db":
            print("Libreria 'psycopg2' no esta instalada. Se continuara en modo local sin base de datos.")
        
    print("=== INICIANDO DESCARGA DE POSTERS ===\n")
    if args.source == "tmdb-popular":
        results = download_popular_posters(limit=args.limit)
    else:
        results = download_posters_for_all_films(conn, limit=args.limit)
    verify_downloaded_posters()
    
    if conn:
        conn.close()
    print("\n=== PROCESO COMPLETADO ===")
