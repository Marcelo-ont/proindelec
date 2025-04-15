# Busca empresas en duckduckgo
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import re
from driver import iniciar_driver
from excel_paths import excel_path__buscador_empresas


def obtener_html(url):
    """Obtiene el HTML de la página usando requests. Si no se obtiene, se pasa al siguiente."""
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://duckduckgo.com/"
}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error al obtener la página: {response.status_code} para {url}")
    except requests.exceptions.RequestException as e:
        print(f"Error de solicitud: {e} para {url}")

    # Si no se pudo obtener el HTML, devolver None
    return None


def buscar_telefono(html):
    """Busca teléfonos en el HTML priorizando <a href="tel:">, enlaces con teléfonos visibles y etiquetas con 'Tel:'."""
    soup = BeautifulSoup(html, 'html.parser')

    # Buscar en <a href="tel:..."> (es la mejor opción)
    for a in soup.find_all('a', href=True):
        if a['href'].startswith("tel:"):
            telefono = re.sub(r'\D', '', a['href'].replace("tel:", ""))  # Solo deja números
            return telefono if telefono else None

    # Buscar en <a> que tengan solo números y guiones
    for a in soup.find_all('a'):
        texto = a.get_text(strip=True)
        if re.fullmatch(r'(\+?\d{1,3}[-.\s]?)?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}', texto):
            return re.sub(r'\D', '', texto)  # Solo deja números

    # Buscar en <p> o <span> que contengan "Tel:"
    for tag in soup.find_all(['p', 'span']):
        texto = tag.get_text(strip=True)
        if "Tel:" in texto or "tel:" in texto.lower():
            telefono = re.search(r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', texto)
            if telefono:
                return re.sub(r'\D', '', telefono.group())  # Solo deja números

    # Como último recurso, usar regex en todo el HTML
    telefono_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}')
    telefonos_regex = telefono_pattern.findall(html)

    # Evitar error "IndexError: string index out of range"
    telefonos_validos = [re.sub(r'\D', '', t[0]) for t in telefonos_regex if t and len(t[0]) > 6 and len(t[0]) < 15]

    return telefonos_validos[0] if telefonos_validos else None


def buscar_email(html):
    """Busca emails en el HTML usando expresiones regulares."""
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    emails = re.findall(email_pattern, html)
    return emails[0] if emails else None


def extraer_datos_kompass_dateas(url):
    """Extrae los datos de teléfono y correo si la URL es de dateas.com o kompass.com."""
    if "dateas.com" in url or "mx.kompass.com" in url:
        html = obtener_html(url)
        if html:  # Solo extrae si se obtuvo el HTML
            telefono = buscar_telefono(html)
            email = buscar_email(html)
            return telefono, email
    return None, None


def extraer_datos(url):
    """Extrae todos los datos de la página usando requests y BeautifulSoup."""
    html = obtener_html(url)
    if not html:
        return None, None

    # Usamos BeautifulSoup para analizar el HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Intentamos buscar teléfono y correo en el HTML
    telefono = buscar_telefono(html)
    email = buscar_email(html)

    return telefono, email


def buscar_empresa(driver, empresa):
    """Busca la empresa en DuckDuckGo y obtiene el primer enlace válido."""
    driver.get("https://duckduckgo.com/")

    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.send_keys(f"{empresa}")
        search_box.send_keys(Keys.RETURN)

        enlaces = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-testid='result-title-a']"))
        )

        ignored_domains = [
            "wikipedia.org", "gasolinamexico.com.mx", "linkedin.com", "dnb.com",
            "indeed.com", "dunsguide.com", "msc.cfe.mx", "quienesquien.wiki",
            "aristeguinoticias.com"
        ]

        for enlace in enlaces:
            url = enlace.get_attribute("href")
            if url and "duckduckgo.com" not in url:
                if any(domain in url.lower() for domain in ignored_domains):
                    continue  # Ignora las URLs con los dominios especificados
                return url

    except Exception as e:
        print(f"Error buscando {empresa}: {e}")
    return "No encontrado"


def main_buscador_empresas():
    archivo_excel = excel_path__buscador_empresas()
    df = pd.read_excel(archivo_excel)

    if "Empresas" not in df.columns:
        print("Error: La columna 'Empresas' no se encuentra en el archivo Excel.")
        return

    # Asegurarse de que las columnas tengan el tipo adecuado
    if "Url" not in df.columns:
        df["Url"] = ""
    if "Telefono" not in df.columns:
        df["Telefono"] = ""
    if "Mail" not in df.columns:
        df["Mail"] = ""

    # Convertir las columnas a tipo str explícitamente para evitar advertencias
    df["Url"] = df["Url"].astype(str)
    df["Telefono"] = df["Telefono"].astype(str)
    df["Mail"] = df["Mail"].astype(str)

    df = df[["Empresas", "Url", "Mail", "Telefono"]]

    driver = iniciar_driver()

    for i, empresa in enumerate(df["Empresas"]):
        print(f"Buscando: {empresa}")
        url = buscar_empresa(driver, empresa)
        df.at[i, "Url"] = str(url)

        # Primero se intenta extraer los datos de dateas.com o kompass.com
        telefono, email = extraer_datos_kompass_dateas(url)
        if telefono or email:
            df.at[i, "Telefono"] = telefono if telefono else ""
            df.at[i, "Mail"] = email if email else ""
        else:
            # Si no es de dateas o kompass, usamos requests y BeautifulSoup para extraer los datos
            telefono, email = extraer_datos(url)
            if telefono or email:
                df.at[i, "Telefono"] = telefono if telefono else ""
                df.at[i, "Mail"] = email if email else ""
            else:
                # Si no se encuentra nada, no ponemos nada en las celdas
                df.at[i, "Telefono"] = ""
                df.at[i, "Mail"] = ""

    driver.quit()
    df.to_excel(archivo_excel, index=False)
    print("Busqueda finalizada. Guardando los resultados en Excel.")


if __name__ == "__main__":
    main_buscador_empresas()
