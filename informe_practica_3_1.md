# Informe final - Practica 3.1 CNN + similitud de coseno

## Objetivo

Se ajusto el proyecto para trabajar con 150 peliculas importadas desde TMDB y ejecutar el modulo 3.1 de la practica: extraccion de embeddings visuales con ResNet-50 preentrenado y recomendacion por similitud de coseno.

## Cambios realizados

- `scripts/04_download_posters.py`: ahora importa por defecto peliculas populares de TMDB con `--source tmdb-popular --limit 150`, descarga posters y genera `data/posters/poster_download_log.csv`.
- `scripts/06_cnn_cosine_recommendations.py`: se ajusto la carga de metadatos para usar el `filename` exacto del log, evitando mezclar posters antiguos con los 150 nuevos.
- `scripts/06_cnn_cosine_recommendations.py`: se mantuvo ResNet-50 preentrenado como extractor de caracteristicas y se limpio la visualizacion t-SNE para titulos con alfabetos no latinos.
- `practica_3_1.ipynb`: se regenero el notebook para documentar y ejecutar el punto 3.1 con 150 posters locales.

## Ejecucion realizada

Comandos ejecutados:

```powershell
python scripts\04_download_posters.py --source tmdb-popular --limit 150
python scripts\06_cnn_cosine_recommendations.py --batch-size 8 --sample-size 20 --strict-pretrained
```

La importacion requirio acceso a internet para consultar TMDB y descargar posters.

## Resultados generados

- `data/posters/poster_download_log.csv`
- `data/processed/visual_embeddings.npy`
- `data/processed/visual_similarity.npy`
- `data/processed/movies_visual_metadata.csv`
- `data/processed/visual_recommendations_top5.csv`
- `data/processed/visual_embeddings_tsne.png`

## Validacion

- Peliculas en log: 150
- Posters descargados segun log: 150/150
- Archivos de poster existentes desde el log: 150/150
- Metadatos usados por CNN: 150 peliculas
- Embeddings visuales: `(150, 2048)`
- Matriz de similitud: `(150, 150)`
- Recomendaciones generadas: 100 filas, equivalentes a top-5 para 20 peliculas de muestra
- Valores NaN en embeddings: 0
- Valores NaN en matriz de similitud: 0
- Diagonal de similitud: minimo `0.99999958`, maximo `1.00000048`
- Rango global de similitud: minimo `0.05546034`, maximo `1.00000048`

## Ejemplo de recomendaciones

Consulta: `Obsesion`

| Rank | Recomendacion | Similitud |
| ---: | --- | ---: |
| 1 | Culpa mia | 0.579900 |
| 2 | Ruta de escape | 0.556302 |
| 3 | Jack Ryan de Tom Clancy: Guerra Encubierta | 0.555209 |
| 4 | Cuenta atras | 0.547394 |
| 5 | Worldbreaker | 0.538666 |

## Conclusion

El punto 3.1 queda completo para 150 peliculas: se importaron los datos visuales, se extrajeron embeddings con ResNet-50 preentrenado, se calculo la matriz de similitud coseno y se generaron recomendaciones cold start. La validacion confirma que los artefactos tienen las dimensiones esperadas y no contienen valores faltantes.
