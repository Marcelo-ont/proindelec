import pandas as pd
from excel_paths import excel_path__buscador_empresas

def main_repetidor_empresas():
    # Rutas de los archivos
    archivo_base_empresas = excel_path__buscador_empresas()
    archivo_base_cfe = r"C:\Users\Ventas3\Documents\base de datos CFE sin repetir.xlsx"

    # Cargar los archivos Excel
    df_empresas = pd.read_excel(archivo_base_empresas)
    df_cfe = pd.read_excel(archivo_base_cfe)

    # Limpiar nombres de columnas
    df_cfe.columns = df_cfe.columns.str.strip()

    # Eliminar duplicados para evitar problemas de índice
    df_cfe = df_cfe.drop_duplicates(subset=['Concursantes'])

    # Crear un diccionario con los datos de la base CFE
    dict_cfe = df_cfe.set_index('Concursantes')[
        ['Contacto del concursante', 'Correo del concursante', 'Telefono del concursante']].to_dict('index')

    # Función para autocompletar datos
    def completar_datos(row):
        empresa = row['Empresas']
        if empresa in dict_cfe:
            row['Url'] = dict_cfe[empresa].get('Contacto del concursante', row['Url'])
            row['Mail'] = dict_cfe[empresa].get('Correo del concursante', row['Mail'])
            row['Telefono'] = dict_cfe[empresa].get('Telefono del concursante', row['Telefono'])
        return row

    # Aplicar la función
    df_empresas = df_empresas.apply(completar_datos, axis=1)

    # Guardar el archivo actualizado
    df_empresas.to_excel(archivo_base_empresas, index=False)

    print("Autocompletado finalizado y guardado en 'base de empresas.xlsx'")


if __name__ == "__main__":
    main_repetidor_empresas()