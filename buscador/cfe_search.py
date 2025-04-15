# Busca empresas en la pagina de CFE
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from driver import iniciar_driver
from excel_paths import excel_path_buscador_cfe


def cargar_pagina(driver, url):
    """Carga la página web especificada."""
    driver.get(url)
    print("Página cargada correctamente.")


def procesar_codigo(codigo, driver):
    """Procesa un código y devuelve su estado, texto adjudicado, descripción y monto adjudicado."""
    try:
        # Esperar y localizar el campo "Número de procedimiento"
        input_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#numProc.form-control"))
        )
        input_box.clear()
        input_box.send_keys(codigo)

        # Esperar y hacer clic en el botón de búsqueda
        buscar_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#buscar.btn.btn-success"))
        )
        buscar_button.click()

        # Esperar la tabla de resultados
        rows = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//tr[@role='row']"))
        )

        # Inicializamos las variables
        texto_adjudicado = None
        descripcion = None
        monto_adjudicado = None

        # Extraer el estado de la octava columna
        for row in rows:
            columnas = row.find_elements(By.TAG_NAME, 'td')
            if len(columnas) > 7:
                estado = columnas[7].text  # Retorna el estado encontrado

                if estado == 'Adjudicado':
                    # Esperar a que el cargador desaparezca
                    WebDriverWait(driver, 20).until(
                        EC.invisibility_of_element((By.ID, "divLoader"))
                    )

                    # Intentar hacer clic en la lupa
                    image_css_selector = "img[src='/Aplicaciones/NCFE/Concursos/Content/img/lupa.png']"
                    lupa = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, image_css_selector))
                    )
                    lupa.click()
                    print(f"Estado '{estado}' encontrado para {codigo}, navegando a la siguiente página.")
                    time.sleep(5)  # Esperar que la nueva página cargue

                    # Cambiar al contexto de la nueva pestaña
                    nueva_pestana = driver.window_handles[-1]
                    driver.switch_to.window(nueva_pestana)

                    try:
                        # Extraer el texto adjudicado
                        adjudicado_text = driver.find_element(By.XPATH, "//td[contains(text(), 'Adjudicado A')]/following-sibling::td").text
                        texto_adjudicado = adjudicado_text.rstrip(',')  # Eliminar la coma final si existe
                        print(f"Texto adjudicado encontrado: {texto_adjudicado}")

                        # Extraer la descripción de la celda siguiente a "Descripción del bien, arrendamiento, servicio, obra ó servicio de obra"
                        descripcion_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Descripción del bien, arrendamiento, servicio, obra ó servicio de obra')]/following-sibling::td")
                        descripcion = descripcion_element.text.strip()  # Quitar cualquier espacio extra
                        print(f"Descripción encontrada: {descripcion}")

                        # Extraer el monto adjudicado (en la fila donde dice 'Monto Adjudicado')
                        monto_element = driver.find_element(By.XPATH, "//tr[td[contains(text(), 'Monto Adjudicado')]]/td[2]")
                        monto_adjudicado = monto_element.text.rstrip(',').strip()
                        print(f"Monto adjudicado encontrado: {monto_adjudicado}")

                    except Exception as e:
                        print(f"Error al extraer datos adicionales: {e}")

                    # Cerrar la pestaña nueva (la que se abre al hacer clic en la lupa)
                    driver.close()

                    # Regresar a la pestaña original (la página de resultados)
                    driver.switch_to.window(driver.window_handles[0])
                    print("Regresando a la página original.")

                return estado, texto_adjudicado, descripcion, monto_adjudicado

        return 'No encontrado', None, None, None  # Valor por defecto si no se encuentra estado

    except Exception as e:
        print(f"Error procesando el código {codigo}: {e}")
        return 'Error', None, None, None


def procesar_codigos(df, driver, codigo_columna, estatus_columna, adjudicado_columna, descripcion_columna, monto_columna):
    """Procesa todos los códigos en el DataFrame y actualiza el estado, texto adjudicado, descripción y monto adjudicado."""
    for index, row in df.iterrows():
        codigo = row[codigo_columna]
        print(f"Procesando código: {codigo}")

        # Intentar hasta 3 veces si falla
        for intento in range(3):
            estado, texto_adjudicado, descripcion, monto_adjudicado = procesar_codigo(codigo, driver)
            if estado not in ['Error', 'No encontrado']:
                df.at[index, estatus_columna] = estado
                df.at[index, adjudicado_columna] = texto_adjudicado if texto_adjudicado else ''
                df.at[index, descripcion_columna] = descripcion if descripcion else ''
                df.at[index, monto_columna] = monto_adjudicado if monto_adjudicado else ''
                print(f"Estatus encontrado para {codigo}: {estado}")
                break
            elif intento < 2:  # Recargar la página para reintentar
                print(f"Reintentando código {codigo}, intento {intento + 1}...")
                driver.refresh()
                time.sleep(5)
        else:
            # Si después de 3 intentos sigue fallando
            df.at[index, estatus_columna] = 'Error'
            df.at[index, adjudicado_columna] = ''
            df.at[index, descripcion_columna] = ''
            df.at[index, monto_columna] = ''
            print(f"No se pudo procesar el código {codigo} después de 3 intentos.")

        time.sleep(3)  # Pausa entre códigos para evitar bloqueos


def guardar_resultados(df, excel_path):
    """Guarda los resultados en el archivo Excel."""
    df.to_excel(excel_path, index=False)
    print("Resultados guardados en el archivo Excel.")


def main_buscador_cfe():
    EXCEL_PATH = excel_path_buscador_cfe()
    URL = "https://msc.cfe.mx/Aplicaciones/NCFE/Concursos/"
    CODIGO_COLUMN_NAME = 'No. De procedimiento'
    ESTATUS_COLUMN_NAME = 'Estatus'
    ADJUDICADO_COLUMN_NAME = 'Texto Adjudicado'
    DESCRIPCION_COLUMN_NAME = 'Descripción'
    MONTO_COLUMN_NAME = 'Monto Adjudicado'

    # Leer archivo Excel
    df = pd.read_excel(EXCEL_PATH)

    # Asegurarse de que las columnas existan
    if ESTATUS_COLUMN_NAME not in df.columns:
        df[ESTATUS_COLUMN_NAME] = ''
    if ADJUDICADO_COLUMN_NAME not in df.columns:
        df[ADJUDICADO_COLUMN_NAME] = ''
    if DESCRIPCION_COLUMN_NAME not in df.columns:
        df[DESCRIPCION_COLUMN_NAME] = ''
    if MONTO_COLUMN_NAME not in df.columns:
        df[MONTO_COLUMN_NAME] = ''

    # Inicializar el driver
    driver = iniciar_driver()

    try:
        # Cargar la página
        cargar_pagina(driver, URL)

        # Procesar códigos
        procesar_codigos(
            df, driver, CODIGO_COLUMN_NAME, ESTATUS_COLUMN_NAME,
            ADJUDICADO_COLUMN_NAME, DESCRIPCION_COLUMN_NAME, MONTO_COLUMN_NAME
        )

    finally:
        # Guardar los resultados y cerrar el driver
        guardar_resultados(df, EXCEL_PATH)
        driver.quit()
        print("Proceso completado.")


if __name__ == "__main__":
    main_buscador_cfe()
