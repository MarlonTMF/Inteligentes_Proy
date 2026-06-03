"""Actualiza dvd_rental_posters.ipynb para DVD Rental + TMDB con meta de 600 posters."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "dvd_rental_posters.ipynb"


def set_source(cell: dict, source: str) -> None:
    cell["source"] = source.strip().splitlines(keepends=True)
    if cell.get("cell_type") == "code":
        cell["execution_count"] = None
        cell["outputs"] = []


nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
cells = nb["cells"]

set_source(
    cells[0],
    """
# CNN + Transformer sobre DVD Rental - Obtencion de Posters

**Proyecto:** CNN + Transformer sobre peliculas  
**Modulo:** Preparacion de posters para la practica 3.1  
**Objetivo:** leer peliculas desde la base DVD Rental, buscar posters en TMDB y generar un log auditable para el modulo CNN + similitud de coseno.
""",
)

set_source(
    cells[7],
    """
## 3. Descarga de Posters desde DVD Rental + TMDB (`scripts/04_download_posters.py`)

Esta seccion sigue la guia del ingeniero: la fuente de peliculas es la tabla `film` de PostgreSQL/DVD Rental y TMDB se usa solo para encontrar metadatos y posters.

### Proceso

1. Consultar `SELECT film_id, title, release_year FROM film ORDER BY film_id`.
2. Buscar cada titulo en TMDB.
3. Descargar el poster en `data/posters`.
4. Guardar `poster_download_log.csv` con `film_id`, `title`, `tmdb_id`, `poster_path`, `filename` y `source_dataset`.
5. Validar la meta de la guia: minimo 600 peliculas procesadas y mas de 90% de posters descargados.
""",
)

set_source(
    cells[8],
    """
import importlib.util
import importlib
import os
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path.cwd()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
config = importlib.reload(config)

if not config.TMDB_API_KEY:
    env_path = PROJECT_ROOT / ".env"
    raise ValueError(
        "TMDB_API_KEY esta vacia. Revisa que exista "
        f"{env_path} y que contenga una linea TMDB_API_KEY=tu_clave."
    )

download_script = PROJECT_ROOT / "scripts" / "04_download_posters.py"

spec = importlib.util.spec_from_file_location("download_posters", download_script)
download_posters = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download_posters)

print("Script cargado:", download_script)
print("TMDB_API_KEY cargada:", bool(config.TMDB_API_KEY), "| longitud:", len(config.TMDB_API_KEY))
print("Funcion disponible:", download_posters.download_posters_for_all_films.__name__)
""",
)

set_source(
    cells[9],
    """
### Ejecucion de descarga desde DVD Rental

Esta celda procesa las primeras **600 peliculas** de DVD Rental. Si un poster ya existe, se reutiliza y se regenera el log.
""",
)

set_source(
    cells[10],
    """
LIMIT = 600

conn = download_posters.connect_to_dvd_rental()
try:
    df_descarga = download_posters.download_posters_for_all_films(conn, limit=LIMIT)
finally:
    conn.close()

downloaded = int(df_descarga["poster_downloaded"].sum())
rate = downloaded / len(df_descarga) if len(df_descarga) else 0
print(f"Peliculas DVD Rental procesadas: {len(df_descarga)}")
print(f"Posters descargados/reutilizados: {downloaded}/{len(df_descarga)} ({rate:.1%})")

display(df_descarga.head(10))
""",
)

set_source(
    cells[11],
    """
### Validacion del log de auditoria

Se comprueba que el CSV tenga al menos 600 filas procesadas, que la tasa de descarga sea superior al 90% y que los archivos indicados por `filename` existan fisicamente en `data/posters`.
""",
)

set_source(
    cells[12],
    """
log_file = Path(config.POSTERS_PATH) / "poster_download_log.csv"

if log_file.exists():
    df_auditoria = pd.read_csv(log_file)
    df_auditoria["poster_file"] = df_auditoria["filename"].map(lambda name: Path(config.POSTERS_PATH) / str(name))
    df_auditoria["file_exists"] = df_auditoria["poster_file"].map(lambda path: path.exists())

    print("Filas en log:", len(df_auditoria))
    print("Posters marcados como descargados:", int(df_auditoria["poster_downloaded"].sum()))
    print("Archivos existentes:", int(df_auditoria["file_exists"].sum()))
    print("Tasa de descarga:", f"{df_auditoria['poster_downloaded'].mean():.1%}")

    assert len(df_auditoria) >= 600, "El log debe contener al menos 600 peliculas de DVD Rental."
    assert df_auditoria["poster_downloaded"].mean() >= 0.90, "La tasa de descarga debe ser al menos 90%."
    assert int(df_auditoria["file_exists"].sum()) == int(df_auditoria["poster_downloaded"].sum()), "Cada poster descargado debe tener archivo fisico."

    display(df_auditoria[["film_id", "title", "release_year", "tmdb_id", "filename", "poster_downloaded", "file_exists"]].head(20))
    display(df_auditoria.loc[~df_auditoria["poster_downloaded"], ["film_id", "title", "release_year"]].head(20))
else:
    raise FileNotFoundError(f"No existe el log esperado: {log_file}")
""",
)

set_source(
    cells[15],
    """
## 5. Checklist de Finalizacion

| Actividad | Completado | Detalle |
| :--- | :---: | :--- |
| Configuracion de rutas y API | **[x]** | `config.py` carga `.env` y rutas locales. |
| Conexion a DVD Rental | **[ ]** | Requiere credenciales PostgreSQL validas en `.env`. |
| Busqueda en TMDB | **[x]** | `scripts/03_tmdb_api.py` implementa cliente y fallback de busqueda. |
| Descarga de posters | **[ ]** | Meta: minimo 600 peliculas procesadas y >90% con poster. |
| Auditoria local | **[ ]** | Validar archivos fisicos desde `poster_download_log.csv`. |
| Preparacion para CNN | **[x]** | Los posters quedan listos para `06_cnn_cosine_recommendations.py`. |
""",
)

NOTEBOOK_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Notebook actualizado: {NOTEBOOK_PATH}")
