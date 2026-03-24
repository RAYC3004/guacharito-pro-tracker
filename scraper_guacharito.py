import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
from datetime import datetime, timedelta
import time

# --- 1. DICCIONARIO MAESTRO COMPLETO ---
ANIMALITOS_MASTER = {
    "0": "DELFIN", "00": "BALLENA", "01": "CARNERO", "02": "TORO", "03": "CIEMPIES",
    "04": "ALACRAN", "05": "LEON", "06": "RANA", "07": "PERICO", "08": "RATON",
    "09": "AGUILA", "10": "TIGRE", "11": "GATO", "12": "CABALLO", "13": "MONO",
    "14": "PALOMA", "15": "ZORRO", "16": "OSO", "17": "PAVO", "18": "BURRO",
    "19": "CHIVO", "20": "CERDO", "21": "GALLO", "22": "CAMELLO", "23": "CEBRA",
    "24": "IGUANA", "25": "GALLINA", "26": "VACA", "27": "PERRO", "28": "ZAMURO",
    "29": "ELEFANTE", "30": "CAIMAN", "31": "LAPA", "32": "ARDILLA", "33": "PESCADO",
    "34": "VENADO", "35": "JIRAFA", "36": "CULEBRA", "37": "TORTUGA", "38": "BUFALO",
    "39": "LECHUZA", "40": "AVISPA", "41": "CANGURO", "42": "TUCAN", "43": "MARIPOSA",
    "44": "CHIGUIRE", "45": "GARZA", "46": "PUMA", "47": "PAVO REAL", "48": "PUERCOESPIN",
    "49": "PEREZA", "50": "CANARIO", "51": "PELICANO", "52": "PULPO", "53": "CARACOL",
    "54": "GRILLO", "55": "OSO HORMIGUERO", "56": "TIBURON", "57": "PATO", "58": "HORMIGA",
    "59": "PANTERA", "60": "CAMALEON", "61": "PANDA", "62": "CACHICAMO", "63": "CANGREJO",
    "64": "GAVILAN", "65": "ARAÑA", "66": "LOBO", "67": "AVESTRUZ", "68": "JAGUAR",
    "69": "CONEJO", "70": "BISONTE", "71": "GUACAMAYA", "72": "GORILA", "73": "HIPOPOTAMO",
    "74": "TURPIAL", "75": "GUACHARO", "76": "RINOCERONTE", "77": "PINGÜINO", "78": "ANTILOPE",
    "79": "CALAMAR", "80": "MURCIELAGO", "81": "CUERVO", "82": "CUCARACHA", "83": "BUHO",
    "84": "CAMARON", "85": "HAMSTER", "86": "BUEY", "87": "CABRA", "88": "ERIZO DE MAR",
    "89": "ANGUILA", "90": "HURON", "91": "MORROCOY", "92": "CISNE", "93": "GAVIOTA",
    "94": "PAUJIL", "95": "ESCARABAJO", "96": "CABALLITO DE MAR", "97": "LORO",
    "98": "COCODRILO", "99": "GUACHARITO"
}

# --- 2. TABLA DEL BRUJO COMPLETA ---
TABLA_BRUJO = [
    ("35", "86"), ("14", "96"), ("02", "46"), ("75", "56"), ("53", "39"), ("37", "52"), 
    ("48", "67"), ("83", "59"), ("94", "91"), ("63", "70"), ("76", "82"), ("50", "65"), 
    ("81", "47"), ("78", "62"), ("89", "71"), ("0", "92"), ("28", "61"), ("09", "38"), 
    ("26", "40"), ("30", "85"), ("11", "69"), ("07", "43"), ("20", "58"), ("32", "41"), 
    ("17", "88"), ("05", "55"), ("22", "72"), ("34", "49"), ("15", "68"), ("03", "98"), 
    ("24", "73"), ("36", "80"), ("13", "57"), ("01", "87"), ("00", "90"), ("27", "95"), 
    ("10", "66"), ("25", "51"), ("29", "44"), ("12", "84"), ("08", "93"), ("19", "64"), 
    ("31", "42"), ("18", "54"), ("06", "74"), ("21", "97"), ("33", "77"), ("16", "60"), 
    ("04", "45"), ("23", "79")
]

URL_BASE = "https://loteriadehoy.com/animalito/elguacharitomillonario/resultados/"

def extraer_datos_por_fecha(dias_atras):
    """Extrae resultados de una fecha específica asegurando la hora real."""
    fecha_dt = datetime.now() - timedelta(days=dias_atras)
    fecha_str = fecha_dt.strftime('%Y-%m-%d')
    
    # Manejo de URLs según la estructura de la página
    if dias_atras == 0:
        url = URL_BASE
    elif dias_atras == 1:
        url = f"{URL_BASE}ayer/"
    else:
        url = f"{URL_BASE}{fecha_str}/"
    
    print(f"Consultando sorteos del día: {fecha_str} en {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        resultados_dia = []
        
        # Estrategia robusta: buscar cualquier etiqueta que contenga una hora (ej. 08:30 AM)
        nodos_hora = soup.find_all(string=re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM)', re.IGNORECASE))
        
        for nodo in nodos_hora:
            # Subir 2 niveles en el HTML para capturar el contenedor completo (Imagen + Texto + Hora)
            padre = nodo.parent.parent
            if padre:
                texto_bloque = padre.get_text(separator=' ', strip=True).upper()
                
                # Buscar el número y el nombre en ese mismo bloque
                match_animal = re.search(r'\b(\d{1,2})\s+([A-ZÁÉÍÓÚÑ]+)\b', texto_bloque)
                match_hora = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', texto_bloque)
                
                if match_animal and match_hora:
                    num = match_animal.group(1).zfill(2) if match_animal.group(1) not in ["0", "00"] else match_animal.group(1)
                    nombre = match_animal.group(2)
                    hora = match_hora.group(1)
                    
                    # Validar estrictamente contra el diccionario maestro para evitar falsos positivos
                    if num in ANIMALITOS_MASTER and ANIMALITOS_MASTER[num] == nombre:
                        resultados_dia.append({
                            "fecha": fecha_str,
                            "hora": hora,
                            "nombre": nombre,
                            "numero": num
                        })
        return resultados_dia
    except Exception as e:
        print(f"Error accediendo a {url}: {e}")
        return []

def validar_teoria_pronostico(df):
    """Verifica la efectividad de la Tabla del Brujo en los últimos 30 días."""
    print("--- Generando Análisis de la Teoría del Brujo ---")
    
    # Filtrar solo el último mes para evaluar
    fecha_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    df_mes = df[df['fecha'] >= fecha_limite]
    
    numeros_sorteados = df_mes['numero'].astype(str).unique()
    
    parejas_completadas = []
    parejas_pendientes = []
    
    for p1, p2 in TABLA_BRUJO:
        if p1 in numeros_sorteados and p2 in numeros_sorteados:
            parejas_completadas.append(f"✅ Completada: {p1} y {p2}")
        else:
            parejas_pendientes.append(f"⏳ Pendiente: {p1} - {p2}")
            
    tasa_exito = (len(parejas_completadas) / len(TABLA_BRUJO)) * 100
    
    # Guardar los resultados en el archivo de texto
    with open('analisis_brujo.txt', 'w', encoding='utf-8') as f:
        f.write(f"=== REPORTE DE EFECTIVIDAD (Últimos 30 días) ===\n")
        f.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n")
        f.write(f"Efectividad de la teoría: {tasa_exito:.1f}%\n")
        f.write(f"Parejas completadas en el mes: {len(parejas_completadas)} de 50\n\n")
        
        f.write("--- PAREJAS COMPLETADAS ---\n")
        f.writelines('\n'.join(parejas_completadas) + '\n\n')
        
        f.write("--- PAREJAS PENDIENTES (Buenas para jugar) ---\n")
        f.writelines('\n'.join(parejas_pendientes) + '\n')

def ejecutar():
    file_name = 'historico_resultados.csv'
    
    # 1. Cargar archivo existente para evitar duplicados
    if os.path.exists(file_name):
        df_historico = pd.read_csv(file_name)
        fechas_ya_descargadas = set(df_historico['fecha'].unique())
    else:
        df_historico = pd.DataFrame(columns=['fecha', 'hora', 'nombre', 'numero'])
        fechas_ya_descargadas = set()

    nuevos_registros = []
    
    # 2. Consultar hasta 1 año (365 días) de manera inteligente
    for i in range(366):
        fecha_evaluar = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Solo extrae si es HOY (i==0) o si la fecha NO está en nuestro CSV
        if i == 0 or fecha_evaluar not in fechas_ya_descargadas:
            datos_dia = extraer_datos_por_fecha(i)
            if datos_dia:
                nuevos_registros.extend(datos_dia)
            time.sleep(1) # Pausa técnica de 1 segundo entre días

    # 3. Consolidar, limpiar y ordenar
    if nuevos_registros:
        df_nuevos = pd.DataFrame(nuevos_registros)
        df_final = pd.concat([df_historico, df_nuevos])
        
        # Eliminar cualquier duplicado exacto
        df_final = df_final.drop_duplicates(subset=['fecha', 'hora', 'numero'])
        
        # Ordenar cronológicamente (Fecha descendente, Hora descendente)
        df_final['hora_temp'] = pd.to_datetime(df_final['hora'], format='%I:%M %p', errors='coerce').dt.time
        df_final = df_final.sort_values(by=['fecha', 'hora_temp'], ascending=[False, False]).drop(columns=['hora_temp'])
        
        df_final.to_csv(file_name, index=False)
        print(f"✅ Archivo CSV actualizado. Total de registros: {len(df_final)}")
        
        # 4. Generar el pronóstico con los datos actualizados
        validar_teoria_pronostico(df_final)
    else:
        print("✅ No se detectaron sorteos nuevos para agregar.")
        # Generamos el pronóstico igual por si fue una ejecución manual
        validar_teoria_pronostico(df_historico)

if __name__ == "__main__":
    ejecutar()
