import json
import os
import re
from typing import List, Dict

RUTA_INDICES = "storage/indices"

# Caché en memoria para no leer el archivo del disco en cada búsqueda
_indices_cargados: Dict[str, List[dict]] = {}

STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", 
    "un", "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", 
    "sus", "le", "ya", "o", "este", "si", "porque", "esta", "son", "entre", "esta"
}

def _limpiar_texto(texto: str) -> str:
    texto = texto.lower()
    # Reemplazar tildes para búsqueda flexible
    reemplazos = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"))
    for a, b in reemplazos:
        texto = texto.replace(a, b)
    return texto

def cargar_indice(taxonomia: str) -> List[dict]:
    """Carga el JSON correspondiente (nanda, noc o nic) una sola vez."""
    taxonomia = taxonomia.lower()
    if taxonomia in _indices_cargados:
        return _indices_cargados[taxonomia]

    ruta_archivo = os.path.join(RUTA_INDICES, f"{taxonomia}.json")
    if not os.path.exists(ruta_archivo):
        print(f"Aviso: No se encontró {ruta_archivo}")
        return []

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)
        _indices_cargados[taxonomia] = datos
        return datos

def buscar_fragmentos(taxonomia: str, consulta: str, top_k: int = 6) -> List[dict]:
    """
    Busca dentro del JSON local los fragmentos con mayor relevancia clínica.
    Filtra páginas iniciales de prólogo/índices y prioriza coincidencias.
    """
    datos = cargar_indice(taxonomia)
    if not datos:
        return []

    consulta_limpia = _limpiar_texto(consulta)
    palabras = [p for p in re.findall(r"\w+", consulta_limpia) if len(p) > 2 and p not in STOPWORDS]

    if not palabras:
        return []

    resultados_con_score = []

    for item in datos:
        texto_raw = item.get("texto", "")
        # Omitir páginas muy cortas o preliminares del libro (portadas/índices)
        if len(texto_raw) < 80 or item.get("pagina", 0) < 15:
            continue

        texto_limpio = _limpiar_texto(texto_raw)
        score = 0

        # Puntuación por coincidencia de palabras clave
        for pal in palabras:
            if pal in texto_limpio:
                score += texto_limpio.count(pal) * 2

        # Puntuación extra si coincide una frase o concepto compuesto
        if len(consulta_limpia) > 5 and consulta_limpia in texto_limpio:
            score += 15

        if score > 0:
            resultados_con_score.append((score, item))

    # Ordenar por mayor puntuación y devolver los mejores fragmentos
    resultados_con_score.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in resultados_con_score[:top_k]]