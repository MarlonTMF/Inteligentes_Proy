"""
Practica 3.1 - CNN + similitud de coseno.

Genera embeddings visuales de posters con ResNet-50 y construye un sistema de
recomendacion cold start usando similitud de coseno.
"""

from __future__ import annotations

import argparse
import os
import unicodedata
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageFile
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

ImageFile.LOAD_TRUNCATED_IMAGES = True


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTERS_DIR = PROJECT_ROOT / "data" / "posters"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_PATH = POSTERS_DIR / "poster_download_log.csv"


class PosterDataset(Dataset):
    def __init__(self, metadata: pd.DataFrame, transform):
        self.metadata = metadata.reset_index(drop=True)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.metadata)

    def __getitem__(self, idx: int):
        row = self.metadata.iloc[idx]
        image = Image.open(row["poster_file"]).convert("RGB")
        return self.transform(image), idx


def find_poster_file(film_id: int, title: str, posters_dir: Path) -> str | None:
    expected_prefix = f"{int(film_id):04d}_"
    matches = sorted(posters_dir.glob(f"{expected_prefix}*.jpg"))
    if matches:
        return str(matches[0])

    safe_title = str(title).replace(" ", "_").replace("/", "_").replace(":", "_")
    matches = sorted(posters_dir.glob(f"*{safe_title}*.jpg"))
    return str(matches[0]) if matches else None


def load_metadata(posters_dir: Path = POSTERS_DIR, log_path: Path = LOG_PATH) -> pd.DataFrame:
    if log_path.exists():
        metadata = pd.read_csv(log_path)
        if "filename" in metadata.columns:
            metadata["poster_file"] = metadata["filename"].map(
                lambda filename: str(posters_dir / str(filename)) if pd.notna(filename) else None
            )
        else:
            metadata["poster_file"] = metadata.apply(
                lambda row: find_poster_file(row["film_id"], row["title"], posters_dir),
                axis=1,
            )
    else:
        rows = []
        for poster in sorted(posters_dir.glob("*.jpg")):
            parts = poster.stem.split("_", 1)
            film_id = int(parts[0]) if parts[0].isdigit() else len(rows) + 1
            title = parts[1].replace("_", " ") if len(parts) > 1 else poster.stem
            rows.append({"film_id": film_id, "title": title, "poster_downloaded": True})
        metadata = pd.DataFrame(rows)
        metadata["poster_file"] = metadata.apply(
            lambda row: find_poster_file(row["film_id"], row["title"], posters_dir),
            axis=1,
        )

    if "poster_downloaded" in metadata.columns:
        metadata = metadata[metadata["poster_downloaded"].astype(bool)]

    metadata = metadata.dropna(subset=["poster_file"]).copy()
    metadata = metadata[metadata["poster_file"].map(lambda path: Path(path).exists())]
    metadata = metadata.sort_values("film_id").reset_index(drop=True)

    if metadata.empty:
        raise FileNotFoundError(
            f"No se encontraron posters JPG en {posters_dir}. Ejecuta primero 04_download_posters.py."
        )

    return metadata


def build_resnet50(device: torch.device, allow_random_fallback: bool = True):
    weights = None
    transform = None

    try:
        weights = models.ResNet50_Weights.DEFAULT
        model = models.resnet50(weights=weights)
        transform = weights.transforms()
        print("Modelo: ResNet-50 preentrenado en ImageNet.")
    except Exception as exc:
        if not allow_random_fallback:
            raise RuntimeError(
                "No se pudo cargar ResNet-50 preentrenado. Revisa internet/cache de torchvision."
            ) from exc

        print("[Warning] No se pudo cargar pesos preentrenados de ResNet-50.")
        print(f"[Warning] Motivo: {exc}")
        print("[Warning] Se usara ResNet-50 sin pesos solo para validar el pipeline local.")
        model = models.resnet50(weights=None)
        transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    model.fc = torch.nn.Identity()
    model.eval()
    model.to(device)
    return model, transform


@torch.no_grad()
def generate_embeddings(
    model: torch.nn.Module,
    dataset: PosterDataset,
    device: torch.device,
    batch_size: int,
    num_workers: int = 0,
) -> np.ndarray:
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )
    embeddings = np.zeros((len(dataset), 2048), dtype=np.float32)

    for images, indices in loader:
        images = images.to(device)
        batch_embeddings = model(images).detach().cpu().numpy().astype(np.float32)
        embeddings[indices.numpy()] = batch_embeddings

    return embeddings


def recommend_by_index(
    movie_idx: int,
    metadata: pd.DataFrame,
    similarity_matrix: np.ndarray,
    top_k: int = 5,
) -> pd.DataFrame:
    similarities = similarity_matrix[movie_idx]
    top_indices = np.argsort(similarities)[::-1]
    top_indices = [idx for idx in top_indices if idx != movie_idx][:top_k]

    result = metadata.iloc[top_indices][["film_id", "title", "poster_file"]].copy()
    result.insert(0, "rank", range(1, len(result) + 1))
    result["similarity"] = similarities[top_indices]
    result.insert(1, "query_title", metadata.iloc[movie_idx]["title"])
    return result


def build_recommendation_table(
    metadata: pd.DataFrame,
    similarity_matrix: np.ndarray,
    top_k: int,
    sample_size: int,
) -> pd.DataFrame:
    rows = []
    for movie_idx in range(min(sample_size, len(metadata))):
        rows.append(recommend_by_index(movie_idx, metadata, similarity_matrix, top_k))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def save_tsne_plot(
    embeddings: np.ndarray,
    metadata: pd.DataFrame,
    output_path: Path,
    max_points: int = 50,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[Warning] matplotlib no esta instalado; se omite t-SNE.")
        return

    n_points = min(max_points, len(metadata))
    if n_points < 3:
        print("[Warning] t-SNE requiere al menos 3 posters; se omite grafico.")
        return

    perplexity = max(2, min(10, n_points - 1))
    coords = TSNE(
        n_components=2,
        perplexity=perplexity,
        init="pca",
        learning_rate="auto",
        random_state=42,
    ).fit_transform(embeddings[:n_points])

    plt.figure(figsize=(12, 8))
    plt.scatter(coords[:, 0], coords[:, 1], s=50, alpha=0.8)
    for idx, title in enumerate(metadata["title"].head(n_points)):
        safe_title = unicodedata.normalize("NFKD", str(title))
        safe_title = safe_title.encode("ascii", "ignore").decode("ascii").strip()
        safe_title = safe_title or f"Movie {idx + 1}"
        plt.annotate(safe_title[:22], (coords[idx, 0], coords[idx, 1]), fontsize=8)
    plt.title("t-SNE de embeddings visuales ResNet-50")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()
    print(f"Grafico t-SNE guardado en: {output_path}")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Practica 3.1 CNN + similitud coseno")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--no-tsne", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument(
        "--strict-pretrained",
        action="store_true",
        help="Falla si no se pueden cargar pesos preentrenados de ResNet-50.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    print(f"Dispositivo: {device}")

    metadata = load_metadata()
    print(f"Posters disponibles: {len(metadata)}")

    model, transform = build_resnet50(
        device=device,
        allow_random_fallback=not args.strict_pretrained,
    )
    dataset = PosterDataset(metadata, transform)

    embeddings = generate_embeddings(
        model=model,
        dataset=dataset,
        device=device,
        batch_size=args.batch_size,
    )
    similarity_matrix = cosine_similarity(embeddings)

    embeddings_path = PROCESSED_DIR / "visual_embeddings.npy"
    similarity_path = PROCESSED_DIR / "visual_similarity.npy"
    metadata_path = PROCESSED_DIR / "movies_visual_metadata.csv"
    recommendations_path = PROCESSED_DIR / "visual_recommendations_top5.csv"
    tsne_path = PROCESSED_DIR / "visual_embeddings_tsne.png"

    np.save(embeddings_path, embeddings)
    np.save(similarity_path, similarity_matrix)
    metadata.to_csv(metadata_path, index=False)

    recommendations = build_recommendation_table(
        metadata=metadata,
        similarity_matrix=similarity_matrix,
        top_k=args.top_k,
        sample_size=args.sample_size,
    )
    recommendations.to_csv(recommendations_path, index=False)

    if not args.no_tsne:
        save_tsne_plot(embeddings, metadata, tsne_path)

    print("\nArchivos generados:")
    print(f"- {embeddings_path}")
    print(f"- {similarity_path}")
    print(f"- {metadata_path}")
    print(f"- {recommendations_path}")

    print("\nEjemplo de recomendaciones cold start:")
    example = recommend_by_index(0, metadata, similarity_matrix, top_k=args.top_k)
    print(example[["rank", "query_title", "title", "similarity"]].to_string(index=False))


if __name__ == "__main__":
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    main()
