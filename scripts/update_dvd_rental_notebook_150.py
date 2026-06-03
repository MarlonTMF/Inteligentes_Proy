"""Actualiza dvd_rental_posters.ipynb para importar 150 peliculas desde TMDB."""

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
# CNN + Transformer sobre DVD Rental/TMDB - Importacion de 150 Posters

**Proyecto:** CNN + Transformer sobre peliculas  
**Modulo:** Preparacion de posters para la practica 3.1  
**Objetivo:** importar 150 peliculas desde TMDB, descargar posters y generar un log auditable para el modulo CNN + similitud de coseno.
""",
)

set_source(
    cells[7],
    """
## 3. Descarga de 150 Posters desde TMDB (`scripts/04_download_posters.py`)

La base PostgreSQL local puede no estar disponible en todos los equipos, por eso este notebook usa TMDB como fuente principal para importar un lote reproducible de **150 peliculas populares**.

### Proceso

1. Consultar `/movie/popular` de TMDB hasta reunir 150 peliculas con poster.
2. Descargar cada poster en `data/posters`.
3. Guardar `poster_download_log.csv` con `film_id`, `title`, `tmdb_id`, `poster_path` y `filename`.
4. Validar que existan exactamente 150 archivos referenciados por el log.
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
print("Funcion disponible:", download_posters.download_popular_posters.__name__)
""",
)

set_source(
    cells[9],
    """
### Ejecucion de descarga/importacion

Esta celda importa **150 peliculas** desde TMDB y descarga sus posters. Si los archivos ya existen, se reutilizan y se regenera el log.
""",
)

set_source(
    cells[10],
    """
LIMIT = 150

df_descarga = download_posters.download_popular_posters(limit=LIMIT)

downloaded = int(df_descarga["poster_downloaded"].sum())
print(f"Peliculas importadas: {len(df_descarga)}")
print(f"Posters descargados/reutilizados: {downloaded}/{LIMIT}")

display(df_descarga.head(10))
""",
)

set_source(
    cells[11],
    """
### Validacion del log de auditoria

Se comprueba que el CSV tenga 150 filas, que todas esten marcadas como descargadas y que los archivos indicados por `filename` existan fisicamente en `data/posters`.
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

    assert len(df_auditoria) == 150, "El log debe contener 150 peliculas."
    assert int(df_auditoria["poster_downloaded"].sum()) == 150, "Deben existir 150 posters descargados."
    assert int(df_auditoria["file_exists"].sum()) == 150, "Deben existir 150 archivos fisicos de poster."

    display(df_auditoria[["film_id", "title", "tmdb_id", "filename", "poster_downloaded", "file_exists"]].head(20))
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
| Importacion desde TMDB | **[x]** | Se importan 150 peliculas populares. |
| Descarga de posters | **[x]** | `poster_download_log.csv` registra 150/150 posters. |
| Auditoria local | **[x]** | Se valida que los 150 archivos existan fisicamente. |
| Preparacion para CNN | **[x]** | Los posters quedan listos para `06_cnn_cosine_recommendations.py`. |
""",
)

NOTEBOOK_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Notebook actualizado: {NOTEBOOK_PATH}")
