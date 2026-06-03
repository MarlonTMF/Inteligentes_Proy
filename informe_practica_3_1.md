# Informe de estado - Practica 3.1 CNN + similitud de coseno

## Objetivo

Se ajusto el proyecto para seguir la guia indicada por el ingeniero: usar DVD Rental como fuente de peliculas, TMDB como fuente de posters y ejecutar el modulo 3.1 con embeddings visuales ResNet-50 + similitud de coseno.

## Cambios realizados

- `scripts/04_download_posters.py`: ahora usa por defecto `--source db --limit 600`, lee peliculas desde PostgreSQL/DVD Rental y busca posters en TMDB.
- `scripts/04_download_posters.py`: se conserva `--source tmdb-popular` solo como respaldo, no como flujo principal de entrega.
- `scripts/04_download_posters.py`: se agrego `connect_to_dvd_rental()` para mostrar un error claro si las credenciales de PostgreSQL no son validas.
- `scripts/06_cnn_cosine_recommendations.py`: se ajusto la carga de metadatos para usar el `filename` exacto del log.
- `scripts/06_cnn_cosine_recommendations.py`: se mantuvo ResNet-50 preentrenado como extractor de caracteristicas y se limpio la visualizacion t-SNE para titulos con alfabetos no latinos.
- `dvd_rental_posters.ipynb`: se actualizo para descargar posters desde DVD Rental + TMDB con meta de 600 peliculas y tasa minima de 90%.
- `practica_3_1.ipynb`: queda como notebook del modulo CNN una vez generado el log correcto de DVD Rental.

## Ejecucion realizada

Comando oficial configurado:

```powershell
python scripts\04_download_posters.py --source db --limit 600
python scripts\06_cnn_cosine_recommendations.py --batch-size 8 --sample-size 20 --strict-pretrained
```

La descarga de 600 posters requiere dos dependencias externas: conexion a PostgreSQL/DVD Rental y acceso a internet para TMDB.

## Estado actual

La ejecucion oficial con DVD Rental esta bloqueada porque el archivo `.env` contiene:

```text
DB_PASSWORD=your_password_here
```

Debe reemplazarse por la contrasena real del usuario `postgres`. Mientras esa credencial no sea correcta, `psycopg2` no puede abrir la conexion a `dvdrental`.

## Resultados generados

- `data/posters/poster_download_log.csv`
- `data/processed/visual_embeddings.npy`
- `data/processed/visual_similarity.npy`
- `data/processed/movies_visual_metadata.csv`
- `data/processed/visual_recommendations_top5.csv`
- `data/processed/visual_embeddings_tsne.png`

## Validacion

- Resultados anteriores disponibles: 150 posters de respaldo desde TMDB popular.
- Resultados oficiales pendientes: 600 peliculas desde DVD Rental.
- Metadatos usados por CNN actualmente: 150 peliculas de respaldo.
- Embeddings visuales actuales: `(150, 2048)`
- Matriz de similitud actual: `(150, 150)`
- Recomendaciones generadas actualmente: 100 filas, equivalentes a top-5 para 20 peliculas de muestra
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

El codigo ya esta corregido para seguir la guia del ingeniero: DVD Rental como fuente de peliculas y TMDB para posters. Falta actualizar `DB_PASSWORD` en `.env`; despues de eso se debe ejecutar `scripts/04_download_posters.py --source db --limit 600` y luego recalcular embeddings con `scripts/06_cnn_cosine_recommendations.py`.
