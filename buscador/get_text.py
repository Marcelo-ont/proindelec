import pdfplumber
import ocrmypdf
import re

# Rutas
ruta_pdf_original = "/home/marcelo/Downloads/PDFActa_245529.pdf"
ruta_pdf_ocr = ruta_pdf_original.replace(".pdf", "_ocr.pdf")

def aplicar_ocr(entrada, salida):
    print("🧠 Aplicando OCR forzado al PDF...")
    ocrmypdf.ocr(entrada, salida, lang='spa', deskew=True, force_ocr=True)
    print("✅ OCR completado:", salida)
    return salida


def extraer_texto_pdf(ruta):
    texto_total = ""
    with pdfplumber.open(ruta) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                texto_total += texto + "\n"
    return texto_total


def limpiar_texto(texto):
    texto = texto.upper()
    texto = re.sub(r'^\s*[A-Z]{1,6}\d{2,}[A-Z0-9]*\s+', '', texto)
    texto = re.sub(r'\b\d+\b', '', texto)
    texto = texto.replace('|', '').replace('[', '').replace(']', '')
    texto = texto.replace('£', '&').replace('T£D', 'T&D').replace('T & D', 'T&D')
    texto = re.sub(r'\s{2,}', ' ', texto)
    return texto.strip()


def extraer_empresas(texto):
    texto = texto.upper().replace('£', '&')

    # Este regex detecta empresas una por una aunque estén pegadas
    patron = r'''
        ([A-Z0-9&ÑÁÉÍÓÚ\s\.\-]+?      # Nombre base
        (?:
            S\.?\s*A\.?\s*DE\s*C\.?\s*V\.? |
            S\.?\s*DE\s*R\.?\s*L\.? |
            EN\s+CONSTRUCCION |
            EN\s+CONSTRUCCIÓN |
            SA\s+DE\s+CV |
            SA\s+DE
        ))
    '''

    matches = re.findall(patron, texto, re.VERBOSE)
    return matches



def main():
    pdf_con_ocr = aplicar_ocr(ruta_pdf_original, ruta_pdf_ocr)
    print("📄 Extrayendo texto del PDF...")
    texto = extraer_texto_pdf(pdf_con_ocr)

    # Limpiar ANTES de deduplicar y ordenar
    empresas_raw = extraer_empresas(texto)
    empresas_limpias = sorted(set(limpiar_texto(e) for e in empresas_raw if limpiar_texto(e)))

    print("\n📋 Lista final de empresas:")
    print("empresas = [")
    for e in empresas_limpias:
        print(f'    "{e}",')
    print("]")


if __name__ == "__main__":
    main()