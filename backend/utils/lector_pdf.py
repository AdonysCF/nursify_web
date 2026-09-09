from pypdf import PdfReader
import io

def extraer_texto_pdf(contenido_bytes: bytes) -> str:
    """Lee el texto plano contenido en los bytes de un archivo PDF."""
    lector = PdfReader(io.BytesIO(contenido_bytes))
    texto = []
    for pagina in lector.pages:
        texto_pagina = pagina.extract_text()
        if texto_pagina:
            texto.append(texto_pagina)
    return "\n".join(texto)