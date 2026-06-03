import json
import os
import shutil

def insert_markdown_cell(notebook_data, index, source_lines):
    cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source_lines]
    }
    # Ensure the last line doesn't have an extra newline if we want it exact, but standard allows it
    notebook_data['cells'].insert(index, cell)

def enrich_dvd_rental(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # 1. Insert theoretical intro for CNN at the beginning (index 1)
    cnn_theory = [
        "## Fundamentos Teóricos: Redes Convolucionales (CNN) y Transfer Learning",
        "",
        "En este módulo aplicamos **Transfer Learning** utilizando **ResNet-50**, una arquitectura de red convolucional profunda preentrenada en ImageNet (1.2 millones de imágenes, 1000 clases).",
        "",
        "### 1. ¿Qué es una CNN?",
        "Las Redes Neuronales Convolucionales (CNN) utilizan capas de convolución que aprenden jerarquías de características visuales. Las primeras capas detectan bordes y texturas, mientras que las capas más profundas identifican partes de objetos.",
        "",
        "### 2. Arquitectura ResNet-50",
        "El mayor desafío de las redes muy profundas es el **desvanecimiento del gradiente**. ResNet resuelve esto mediante *conexiones residuales* (skip connections), que permiten que el gradiente fluya directamente a través de las capas sin multiplicarse por pesos pequeños constantemente.",
        "",
        "### 3. Similitud de Coseno",
        "Una vez extraídos los embeddings visuales (vectores de 2048 dimensiones de la penúltima capa de ResNet-50), medimos la similitud entre dos películas $A$ y $B$ calculando el coseno del ángulo entre sus vectores:",
        "",
        "$$ \\text{coseno}(A,B) = \\frac{A \\cdot B}{\\|A\\| \\|B\\|} $$",
        "",
        "Los valores oscilan entre -1 y 1. Dado que usamos activaciones ReLU, los embeddings son no negativos, resultando en valores en el rango $[0, 1]$, donde $1$ indica identidad visual perfecta."
    ]
    
    insert_markdown_cell(nb, 1, cnn_theory)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Enriched {filepath}")

def enrich_pipeline(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # We will insert DistilBERT theory before Parte 3
    # Find Parte 3
    idx_p3 = -1
    for i, c in enumerate(nb['cells']):
        if c['cell_type'] == 'markdown' and 'Parte 3:' in ''.join(c['source']):
            idx_p3 = i
            break
            
    if idx_p3 != -1:
        distil_theory = [
            "## Fundamentos Teóricos: Transformers y DistilBERT",
            "",
            "Para el procesamiento de las reseñas (lenguaje natural), utilizamos una arquitectura **Transformer**.",
            "",
            "### 1. Mecanismo de Auto-Atención",
            "La auto-atención permite que el modelo pondere la importancia de cada palabra en una secuencia respecto a todas las demás, capturando el contexto global de la reseña. Su ecuación principal es:",
            "",
            "$$ \\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V $$",
            "",
            "### 2. DistilBERT vs BERT",
            "**DistilBERT** es una versión *destilada* de BERT. Es un 40% más pequeña y un 60% más rápida, pero mantiene el 97% del rendimiento del modelo original. Utilizamos el token especial `[CLS]` (clasificación) del output de DistilBERT como un **embedding denso de 768 dimensiones** que resume semánticamente toda la reseña."
        ]
        insert_markdown_cell(nb, idx_p3, distil_theory)
    
    # Re-find cells for GRU theory
    idx_p5 = -1
    for i, c in enumerate(nb['cells']):
        if c['cell_type'] == 'markdown' and 'Parte 5:' in ''.join(c['source']):
            idx_p5 = i
            break
            
    if idx_p5 != -1:
        gru_theory = [
            "## Fundamentos Teóricos: Redes Recurrentes (GRU) y Eigenvalores",
            "",
            "Para modelar el comportamiento secuencial del usuario (el orden en que ve las películas), utilizamos redes recurrentes.",
            "",
            "### 1. El Problema de las RNN Simples",
            "Las RNN estándar sufren del **desvanecimiento o explosión del gradiente**. Matemáticamente, durante *Backpropagation Through Time (BPTT)*, se multiplica repetidamente la matriz Jacobiana $W$. ",
            "Si los eigenvalores $\\lambda_i$ de esta matriz cumplen $|\\lambda_i| > 1$, la norma del gradiente crece exponencialmente (explosión). Si $|\\lambda_i| < 1$, el gradiente se desvanece y la red olvida el contexto a largo plazo.",
            "",
            "### 2. Gated Recurrent Unit (GRU)",
            "La arquitectura GRU soluciona esto introduciendo *compuertas* que regulan el flujo de información:",
            "- **Update Gate ($z_t$):** Decide cuánta información pasada mantener.",
            "- **Reset Gate ($r_t$):** Decide cuánta información pasada olvidar.",
            "",
            "Ecuación simplificada de la memoria en GRU/LSTM:",
            "$$ f_t = \\sigma(W_f \\cdot [h_{t-1}, x_t] + b_f) $$",
            "",
            "A diferencia de LSTM (que tiene 3 compuertas y una celda de estado independiente), GRU es más rápida de entrenar y requiere menos memoria, lo cual es ideal para secuencias de historial de usuarios cortas/medias."
        ]
        insert_markdown_cell(nb, idx_p5, gru_theory)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Enriched {filepath}")

def enrich_integracion(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    idx_p5 = -1
    for i, c in enumerate(nb['cells']):
        if c['cell_type'] == 'markdown' and 'Parte 5:' in ''.join(c['source']):
            idx_p5 = i
            break
            
    if idx_p5 != -1:
        inte_theory = [
            "## Fundamentos Teóricos: Integración Multimodal Trimodal",
            "",
            "En esta sección fusionamos los conocimientos extraídos de múltiples modalidades:",
            "1. **Visión (Pósters):** ResNet-50 (2048 dimensiones).",
            "2. **Texto (Reseñas):** DistilBERT (768 dimensiones).",
            "",
            "### Estrategia de Fusión",
            "Implementamos una **fusión temprana a nivel de características (Late-to-Early Fusion)** concatenando los vectores normalizados (L2) de ambas modalidades. La normalización es crucial para evitar que el espacio de 2048 dimensiones de ResNet domine la métrica del coseno sobre el de 768 dimensiones de DistilBERT.",
            "",
            "### Métricas de Evaluación Cuantitativa",
            "1. **Precisión@K:** Medida de cuántas recomendaciones en el top $K$ son relevantes para el usuario.",
            "2. **NDCG@K:** Considera el orden (ranking) de las recomendaciones, penalizando fuertemente los aciertos que aparecen en las posiciones inferiores.",
            "3. **Silhouette Score:** Evaluaremos la calidad del agrupamiento de los embeddings en el espacio t-SNE, verificando si las películas de géneros similares se agrupan en clusters densos y separados."
        ]
        insert_markdown_cell(nb, idx_p5, inte_theory)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Enriched {filepath}")

if __name__ == '__main__':
    # Move the file from SIS-INTE first
    src = "SIS-INTE/movie_recommendation_pipeline.ipynb"
    dst = "movie_recommendation_pipeline.ipynb"
    shutil.copy(src, dst)
    print("Copied pipeline notebook to root.")
    
    enrich_dvd_rental("dvd_rental_posters.ipynb")
    enrich_pipeline("movie_recommendation_pipeline.ipynb")
    enrich_integracion("integracion_evaluacion.ipynb")

