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

def connect_to_dvd_rental():
    """Abre conexion a PostgreSQL/DVD Rental con un mensaje de error entendible."""
    if psycopg2 is None:
        raise RuntimeError("Libreria 'psycopg2' no esta instalada; no se puede usar DVD Rental.")

    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        raise RuntimeError(
            "No se pudo conectar a PostgreSQL/DVD Rental. Revisa el archivo .env, "
            "especialmente DB_PASSWORD. Actualmente debe contener la contrasena real "
            "del usuario PostgreSQL, no 'your_password_here'."
        ) from e


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

def get_films_from_db(conn, limit=None):
    """Obtiene peliculas de la tabla film de DVD Rental."""
    query = "SELECT film_id, title, release_year FROM film ORDER BY film_id"
    films = pd.read_sql(query, conn)

    if limit:
        films = films.head(limit)

    return films

def get_films_from_csv(limit=None):
    """Obtiene peliculas simulando DVD Rental desde un CSV local."""
    csv_path = os.path.join(PROJECT_ROOT, "data", "raw", "film.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"El archivo {csv_path} no existe. Por favor, descargalo primero.")
    
    films = pd.read_csv(csv_path)
    if limit:
        films = films.head(limit)
    return films


def download_posters_for_all_films(conn=None, limit=600, use_csv=False):
    """Busca y descarga posters para peliculas de DVD Rental usando TMDB."""
    if use_csv:
        films = get_films_from_csv(limit=limit)
    else:
        if conn is None:
            raise ValueError("Se requiere una conexion activa a PostgreSQL/DVD Rental.")
        films = get_films_from_db(conn, limit=limit)
        
    print(f"Procesando {len(films)} peliculas desde DVD Rental...")
    client = TMDBClient(TMDB_API_KEY)
    results = []
    
    for _, row in tqdm(films.iterrows(), total=len(films)):
        film_id = int(row['film_id'])
        title = str(row['title'])
        year = int(row['release_year']) if pd.notnull(row['release_year']) else None
        
        result = {
            'film_id': film_id,
            'title': title,
            'release_year': year,
            'poster_downloaded': False,
            'tmdb_id': None,
            'poster_path': None,
            'filename': None,
            'source_dataset': 'dvd_rental'
        }
        
        tmdb_movie = search_film_in_tmdb(client, title, year)
        if tmdb_movie:
            poster_path = tmdb_movie.get('poster_path')
            if poster_path:
                poster_url = client.get_poster_url(poster_path)
                filename = get_poster_filename(film_id, title)
                save_path = os.path.join(POSTERS_PATH, filename)

                if os.path.exists(save_path) or download_image(poster_url, save_path):
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
            "source_dataset": "tmdb_popular",
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

def verify_downloaded_posters(log_df=None):
    """Verifica posters descargados; si hay log, valida los archivos referenciados."""
    if log_df is not None and "filename" in log_df.columns:
        valid_filenames = log_df.dropna(subset=["filename"])["filename"]
        existing = sum(
            os.path.exists(os.path.join(POSTERS_PATH, str(filename)))
            for filename in valid_filenames
        )
        print(f"Archivos referenciados por log: {existing}/{len(valid_filenames)}")
        return existing

    poster_files = os.listdir(POSTERS_PATH)
    jpg_files = [f for f in poster_files if f.endswith('.jpg')]
    print(f"Archivos JPG en carpeta: {len(jpg_files)}")
    return len(jpg_files)

def parse_args():
    parser = argparse.ArgumentParser(description="Importa peliculas y descarga posters.")
    parser.add_argument("--limit", type=int, default=600)
    parser.add_argument(
        "--source",
        choices=["tmdb-popular", "db", "csv"],
        default="csv",
        help="csv usa archivo local simulando BD; db usa PostgreSQL real; tmdb-popular usa web.",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    conn = None
    if args.source == "db":
        conn = connect_to_dvd_rental()
        print("Conexion establecida con la base de datos PostgreSQL.")
        
    print("=== INICIANDO DESCARGA DE POSTERS ===\n")
    if args.source == "tmdb-popular":
        results = download_popular_posters(limit=args.limit)
    elif args.source == "csv":
        results = download_posters_for_all_films(conn=None, limit=args.limit, use_csv=True)
    else:
        results = download_posters_for_all_films(conn, limit=args.limit, use_csv=False)
    verify_downloaded_posters(results)
    
    if conn:
        conn.close()
    print("\n=== PROCESO COMPLETADO ===")
