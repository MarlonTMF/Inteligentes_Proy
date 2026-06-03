import importlib.util
import os
import sys

# Determinar la ruta al archivo real 03_tmdb_api.py
current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(current_dir, "03_tmdb_api.py")

# Cargar dinamicamente para evitar errores sintacticos por el nombre que inicia con digitos
spec = importlib.util.spec_from_file_location("tmdb_api_03", module_path)
tmdb_module = importlib.util.module_from_spec(spec)
sys.modules["tmdb_api_03"] = tmdb_module
spec.loader.exec_module(tmdb_module)

# Exponer las clases y funciones importadas de manera transparente
TMDBClient = tmdb_module.TMDBClient
search_film_in_tmdb = tmdb_module.search_film_in_tmdb
get_all_films_from_db = tmdb_module.get_all_films_from_db
