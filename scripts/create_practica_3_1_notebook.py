"""Crea el notebook de entrega para la practica 3.1."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "practica_3_1.ipynb"


def markdown(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.strip().splitlines(keepends=True),
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip().splitlines(keepends=True),
    }


cells = [
    markdown(
        """
# Practica 3.1 - CNN + similitud de coseno

**Deep Learning Multimodal: CNN + Transformers**

Este notebook implementa el punto **3.1 CNN + similitud de coseno** de la practica:

1. Carga 150 posters locales de peliculas importadas desde TMDB.
2. Usa **ResNet-50 preentrenado en ImageNet** como extractor visual.
3. Genera embeddings visuales de 2048 dimensiones.
4. Calcula similitud de coseno entre peliculas.
5. Recomienda las top-K peliculas mas similares para cold start.
6. Guarda resultados en `data/processed`.
"""
    ),
    markdown(
        """
## 1. Configuracion

Si ejecutas en Colab, activa GPU. En esta maquina tambien funciona en CPU, solo tarda un poco mas.
"""
    ),
    code(
        """
from pathlib import Path
import os
import sys

PROJECT_ROOT = Path.cwd()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

POSTERS_DIR = PROJECT_ROOT / "data" / "posters"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("Proyecto:", PROJECT_ROOT)
print("Posters:", POSTERS_DIR)
print("Salida:", PROCESSED_DIR)
"""
    ),
    code(
        """
import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
"""
    ),
    markdown(
        """
## 2. Cargar metadatos de posters

Se usa `poster_download_log.csv` y los archivos `.jpg` de `data/posters`.
"""
    ),
    code(
        """
import importlib.util

script_path = PROJECT_ROOT / "scripts" / "06_cnn_cosine_recommendations.py"
spec = importlib.util.spec_from_file_location("cnn_cosine", script_path)
cnn_cosine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cnn_cosine)

metadata = cnn_cosine.load_metadata()
metadata[["film_id", "title", "poster_file"]].head()
"""
    ),
    code(
        """
print(f"Posters disponibles: {len(metadata)}")
metadata[["film_id", "title"]].head(10)
"""
    ),
    markdown(
        """
## 3. Cargar ResNet-50 preentrenado

Quitamos la capa final (`fc`) y usamos la salida anterior como embedding visual de 2048 dimensiones.
"""
    ),
    code(
        """
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Dispositivo:", device)

model, transform = cnn_cosine.build_resnet50(device=device, allow_random_fallback=False)
model
"""
    ),
    markdown(
        """
## 4. Descargar/preprocesar posters

En este proyecto los posters ya estan descargados. El preprocesamiento se aplica con las transformaciones oficiales de los pesos de ResNet-50.
"""
    ),
    code(
        """
from IPython.display import display

for poster_path in metadata["poster_file"].head(3):
    image = Image.open(poster_path).convert("RGB")
    image.thumbnail((150, 220))
    display(image)
"""
    ),
    markdown(
        """
## 5. Generar embeddings visuales
"""
    ),
    code(
        """
dataset = cnn_cosine.PosterDataset(metadata, transform)
visual_embeddings = cnn_cosine.generate_embeddings(
    model=model,
    dataset=dataset,
    device=device,
    batch_size=4,
)

visual_embeddings.shape
"""
    ),
    code(
        """
np.save(PROCESSED_DIR / "visual_embeddings.npy", visual_embeddings)
metadata.to_csv(PROCESSED_DIR / "movies_visual_metadata.csv", index=False)

print("Guardado:", PROCESSED_DIR / "visual_embeddings.npy")
print("Guardado:", PROCESSED_DIR / "movies_visual_metadata.csv")
"""
    ),
    markdown(
        """
## 6. Calcular matriz de similitud coseno

La similitud de coseno mide el angulo entre dos embeddings:

\\[
cos(A,B)=\\frac{A \\cdot B}{\\|A\\|\\|B\\|}
\\]
"""
    ),
    code(
        """
visual_similarity = cosine_similarity(visual_embeddings)
np.save(PROCESSED_DIR / "visual_similarity.npy", visual_similarity)

print("Matriz:", visual_similarity.shape)
print("Similitud pelicula 0 consigo misma:", visual_similarity[0, 0])
"""
    ),
    markdown(
        """
## 7. Sistema de recomendacion cold start

Dada una pelicula, se devuelven las top-K mas similares visualmente.
"""
    ),
    code(
        """
def recommend_visual(movie_idx, top_k=5):
    return cnn_cosine.recommend_by_index(
        movie_idx=movie_idx,
        metadata=metadata,
        similarity_matrix=visual_similarity,
        top_k=top_k,
    )

recommend_visual(0, top_k=5)[["rank", "query_title", "title", "similarity"]]
"""
    ),
    code(
        """
all_recommendations = cnn_cosine.build_recommendation_table(
    metadata=metadata,
    similarity_matrix=visual_similarity,
    top_k=5,
    sample_size=10,
)
all_recommendations.to_csv(PROCESSED_DIR / "visual_recommendations_top5.csv", index=False)
all_recommendations.head(15)
"""
    ),
    markdown(
        """
## 8. Visualizacion cualitativa de recomendaciones
"""
    ),
    code(
        """
import matplotlib.pyplot as plt

def show_recommendations(movie_idx, top_k=5):
    recs = recommend_visual(movie_idx, top_k=top_k)
    rows = [metadata.iloc[movie_idx]] + [
        metadata.iloc[metadata.index[metadata["film_id"] == film_id][0]]
        for film_id in recs["film_id"]
    ]
    titles = ["Consulta"] + [f"Top {rank}" for rank in recs["rank"]]

    plt.figure(figsize=(2.3 * len(rows), 4.2))
    for i, row in enumerate(rows):
        image = Image.open(row["poster_file"]).convert("RGB")
        ax = plt.subplot(1, len(rows), i + 1)
        ax.imshow(image)
        ax.set_title(f"{titles[i]}\\n{row['title']}", fontsize=9)
        ax.axis("off")
    plt.tight_layout()

show_recommendations(0, top_k=5)
"""
    ),
    markdown(
        """
## 9. t-SNE opcional

Proyecta los embeddings de 2048 dimensiones a 2D para inspeccionar grupos visuales.
"""
    ),
    code(
        """
cnn_cosine.save_tsne_plot(
    embeddings=visual_embeddings,
    metadata=metadata,
    output_path=PROCESSED_DIR / "visual_embeddings_tsne.png",
)

img = Image.open(PROCESSED_DIR / "visual_embeddings_tsne.png")
display(img)
"""
    ),
    markdown(
        """
## Resultados generados

- `data/processed/visual_embeddings.npy`
- `data/processed/visual_similarity.npy`
- `data/processed/movies_visual_metadata.csv`
- `data/processed/visual_recommendations_top5.csv`
- `data/processed/visual_embeddings_tsne.png`

Con esto queda cubierto el punto **3.1 CNN + similitud de coseno**: modelo ResNet-50, preprocesamiento de posters, embeddings, matriz coseno, recomendador top-K y visualizacion.
"""
    ),
]


notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.12",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Notebook creado: {NOTEBOOK_PATH}")
