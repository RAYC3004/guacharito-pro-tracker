import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
from datetime import datetime, timedelta
import time
from google import genai

# --- 1. DICCIONARIO MAESTRO ---
ANIMALITOS_MASTER = {
    "0": "DELFIN", "00": "BALLENA", "01": "CARNERO", "02": "TORO", "03": "CIEMPIES", "04": "ALACRAN", "05": "LEON", "06": "RANA", "07": "PERICO", "08": "RATON",
    "09": "AGUILA", "10": "TIGRE", "11": "GATO", "12": "CABALLO", "13": "MONO", "14": "PALOMA", "15": "ZORRO", "16": "OSO", "17": "PAVO", "18": "BURRO",
    "19": "CHIVO", "20": "CERDO", "21": "GALLO", "22": "CAMELLO", "23": "CEBRA", "24": "IGUANA", "25": "GALLINA", "26": "VACA", "27": "PERRO", "28": "ZAMURO",
    "29": "ELEFANTE", "30": "CAIMAN", "31": "LAPA", "32": "ARDILLA", "33": "PESCADO", "34": "VENADO", "35": "JIRAFA", "36": "CULEBRA", "37": "TORTUGA", "38": "BUFALO",
    "39": "LECHUZA", "40": "AVISPA", "41": "CANGURO", "42": "TUCAN", "43": "MARIPOSA", "44": "CHIGUIRE", "45": "GARZA", "46": "PUMA", "47": "PAVO REAL", "48": "PUERCOESPIN",
    "49": "PEREZA", "50": "CANARIO", "51": "PELICANO", "52": "PULPO", "53": "CARACOL", "54": "GRILLO", "55": "OSO HORMIGUERO", "56": "TIBURON", "57": "PATO", "58": "HORMIGA",
    "59": "PANTERA", "60": "CAMALEON", "61": "PANDA", "62": "CACHICAMO", "63": "CANGREJO", "64": "GAVILAN", "65": "ARAÑA", "66": "LOBO", "67": "AVESTRUZ", "68": "JAGUAR",
    "69": "CONEJO", "70": "BISONTE", "71": "GUACAMAYA", "72": "GORILA", "73": "HIPOPOTAMO", "74": "TURPIAL", "75": "GUACHARO", "76": "RINOCERONTE", "77": "PINGÜINO", "78": "ANTILOPE",
    "79": "CALAMAR", "80": "MURCIELAGO", "81": "CUERVO", "82": "CUCARACHA", "83": "BUHO", "84": "CAMARON", "85": "HAMSTER", "86": "BUEY", "87": "CABRA", "88": "ERIZO DE MAR",
    "89": "ANGUILA", "90": "HURON", "91": "MORROCOY", "92": "CISNE", "93": "GAVIOTA", "94": "PAUJIL", "95": "ESCARABAJO", "96": "CABALLITO DE MAR", "97": "LORO", "98": "COCODRILO", "99": "GUACHARITO"
}

# --- 2. TABLA DEL BRUJO ---
TABLA_BRUJO = [
    ("35", "86"), ("14", "96"), ("02", "46"), ("75", "56"), ("53", "39"), ("37", "52"), ("48", "67"), ("83", "59"), ("94", "91"), ("63", "70"), 
    ("76", "82"), ("50", "65"), ("81", "47"), ("78", "62"), ("89", "71"), ("0", "92"), ("28", "61"), ("09", "38"), ("26", "40"), ("30", "85"), 
    ("11", "69"), ("07", "43"), ("20", "58"), ("32", "41"), ("17", "88"), ("05", "55"), ("22", "72"), ("34", "49"), ("15", "68"), ("03", "98"), 
    ("24", "73"), ("36", "80"), ("13", "57"), ("01", "87"), ("00", "90"), ("27", "95"), ("10", "66"), ("25", "51"), ("29", "44"), ("12", "84"), 
    ("08", "93"), ("19", "64"), ("31", "42"), ("18", "54"), ("06", "74"), ("21", "97"), ("33", "77"), ("16", "60"), ("04", "45"), ("23", "79")
]

URL_BASE = "https://loteriadehoy.com/animalito/elguacharitomillonario/resultados/"

def extraer_datos_por_fecha(dias_atras):
    fecha_dt = datetime.now() - timedelta(days=dias_atras)
    fecha_str = fecha_dt.strftime('%Y-%m-%d')
    url = URL_BASE if dias_atras == 0 else (f"{URL_BASE}ayer/" if dias_atras == 1 else f"{URL_BASE}{fecha_str}/")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        resultados_dia = []
        nodos_hora = soup.find_all(string=re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM)', re.IGNORECASE))
        
        for nodo in nodos_hora:
            padre = nodo.parent.parent
            if padre:
                texto_bloque = padre.get_text(separator=' ', strip=True).upper()
                match_animal = re.search(r'\b(\d{1,2})\s+([A-ZÁÉÍÓÚÑ]+)\b', texto_bloque)
                match_hora = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', texto_bloque)
                
                if match_animal and match_hora:
                    num = match_animal.group(1).zfill(2) if match_animal.group(1) not in ["0", "00"] else match_animal.group(1)
                    nombre = match_animal.group(2)
                    hora = match_hora.group(1)
                    
                    if num in ANIMALITOS_MASTER and ANIMALITOS_MASTER[num] == nombre:
                        resultados_dia.append({"fecha": fecha_str, "hora": hora, "nombre": nombre, "numero": num})
        return resultados_dia
    except Exception as e:
        return []

def limpiar_formato_numero(x):
    val = str(x).strip()
    if val.endswith('.0'): val = val[:-2]
    if val in ["0", "00"]: return val
    return val.zfill(2)

def obtener_pareja_del_brujo(numero):
    for p1, p2 in TABLA_BRUJO:
        if numero == p1 or numero == p2:
            return p1, p2
    return None, None

def enviar_mensaje_telegram(mensaje):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': mensaje, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def verificar_y_notificar_bingo(df_viejo, nuevos_registros):
    if df_viejo.empty or not nuevos_registros:
        return

    fecha_hoy_str = datetime.now().strftime('%Y-%m-%d')
    registros_hoy = [r for r in nuevos_registros if r['fecha'] == fecha_hoy_str]
    
    if not registros_hoy:
        return

    df_viejo['fecha'] = pd.to_datetime(df_viejo['fecha'], format='mixed', errors='coerce')
    fecha_hoy_dt = datetime.now()
    ultimas_salidas = df_viejo.groupby('numero')['fecha'].max()

    mensajes_bingo = []

    for reg in registros_hoy:
        num = reg['numero']
        p1, p2 = obtener_pareja_del_brujo(num)
        
        if p1 and p2:
            fecha_p1 = ultimas_salidas.get(p1, fecha_hoy_dt - timedelta(days=999))
            fecha_p2 = ultimas_salidas.get(p2, fecha_hoy_dt - timedelta(days=999))
            dias_sin_salir = min((fecha_hoy_dt - fecha_p1).days, (fecha_hoy_dt - fecha_p2).days)

            if dias_sin_salir >= 15:
                mensajes_bingo.append(f"🎯 <b>¡BINGO DE ALERTA ROJA!</b>\nSalió el <b>{num} ({reg['nombre']})</b> a las {reg['hora']}.\n¡La pareja {p1}-{p2} rompió su racha de {dias_sin_salir} días invicta! A COBRAR 💸")
            
            elif 7 <= dias_sin_salir <= 14:
                mensajes_bingo.append(f"⚠️ <b>¡BINGO DE ALERTA AMARILLA!</b>\nSalió el <b>{num} ({reg['nombre']})</b> a las {reg['hora']}.\nLa pareja {p1}-{p2} reventó tras {dias_sin_salir} días en observación. ✅")

    if mensajes_bingo:
        mensaje_final = "🎉🎉 <b>¡EL BRUJO TENÍA RAZÓN!</b> 🎉🎉\n\n" + "\n\n".join(mensajes_bingo)
        enviar_mensaje_telegram(mensaje_final)
        time.sleep(2)

def generar_consejo_ia(rojas, amarillas, verdes):
    api_key = os.environ.get("GEMINI_API_KEY")
    mensaje_respaldo = "La energía está concentrada en los números. Sigue la tabla."
    
    if not api_key:
        with open('mensaje_brujo.txt', 'w', encoding='utf-8') as f:
            f.write(mensaje_respaldo)
        return f"📊 <b>ANÁLISIS ESTRATÉGICO:</b>\n<i>\"{mensaje_respaldo}\"</i>\n"
    
    top_rojas = ", ".join([r.split('</b>')[0].replace('🔴 <b>', '') for r in rojas[:3]]) if rojas else "Ninguna"
    top_amarillas = ", ".join([a.split(' (')[0].replace('🟡 ', '') for a in amarillas[:3]]) if amarillas else "Ninguna"
    
    contexto_datos = f"Alertas Rojas actuales (Más de 15 días sin salir): {top_rojas}. Alertas Amarillas (calentando): {top_amarillas}. Total descartadas: {len(verdes)}."

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"Actúa como el Brujo Guacharito, experto estadístico de lotería. Basado ESTRICTAMENTE en estos datos de hoy: '{contexto_datos}', escribe una recomendación estratégica de máximo 2 líneas. Sé directo, persuasivo y usa un par de emojis. No uses saludos."
        respuesta = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        mensaje_magico = respuesta.text.strip()
        
        with open('mensaje_brujo.txt', 'w', encoding='utf-8') as f:
            f.write(mensaje_magico)
        return f"📊 <b>ANÁLISIS ESTRATÉGICO:</b>\n<i>\"{mensaje_magico}\"</i>\n"
    except Exception as e:
        with open('mensaje_brujo.txt', 'w', encoding='utf-8') as f:
            f.write(mensaje_respaldo)
        return f"📊 <b>ANÁLISIS ESTRATÉGICO:</b>\n<i>\"{mensaje_respaldo}\"</i>\n"

def validar_teoria_pronostico(df):
    df['fecha'] = pd.to_datetime(df['fecha'], format='mixed', errors='coerce')
    df['numero'] = df['numero'].apply(limpiar_formato_numero)
    fecha_hoy = datetime.now()
    ultimas_salidas = df.groupby('numero')['fecha'].max()
    
    parejas_rojas, parejas_amarillas, parejas_verdes = [], [], []
    parejas_quemadas = 0   
    
    for p1, p2 in TABLA_BRUJO:
        fecha_p1 = ultimas_salidas.get(p1, fecha_hoy - timedelta(days=999))
        fecha_p2 = ultimas_salidas.get(p2, fecha_hoy - timedelta(days=999))
        dias_sin_salir = min((fecha_hoy - fecha_p1).days, (fecha_hoy - fecha_p2).days)
        
        if dias_sin_salir >= 15:
            dias_mostrar = "Más de 30" if dias_sin_salir == 999 else dias_sin_salir
            parejas_rojas.append(f"🔴 <b>{p1} - {p2}</b> ({dias_mostrar} días)")
        elif 7 <= dias_sin_salir <= 14:
            parejas_amarillas.append(f"🟡 {p1} - {p2} ({dias_sin_salir} días)")
        elif 1 <= dias_sin_salir <= 6:
            parejas_verdes.append(f"🟢 {p1} - {p2} ({dias_sin_salir} días)")
        else:
            parejas_quemadas += 1

    mensaje_ia = generar_consejo_ia(parejas_rojas, parejas_amarillas, parejas_verdes)

    mensaje = f"🚨 <b>REPORTE DEL BRUJO</b> 🚨\n"
    mensaje += f"📅 Fecha: {fecha_hoy.strftime('%Y-%m-%d %I:%M %p')}\n"
    mensaje += "➖➖➖➖➖➖➖➖➖➖\n"
    mensaje += f"{mensaje_ia}\n" 
    mensaje += "➖➖➖➖➖➖➖➖➖➖\n\n"
    mensaje += f"🔥 Descartadas hoy: {parejas_quemadas} de 50\n\n"
    
    if parejas_rojas:
        mensaje += "🎯 <b>ALERTA ROJA (JUGAR FUERTE)</b>\n" + '\n'.join(parejas_rojas) + "\n\n"
    if parejas_amarillas:
        mensaje += "⚠️ <b>ALERTA AMARILLA (OBSERVAR)</b>\n" + '\n'.join(parejas_amarillas) + "\n\n"
    if parejas_verdes:
        mensaje += "✅ <b>ALERTA VERDE (FRÍAS)</b>\n" + '\n'.join(parejas_verdes) + "\n"

    with open('analisis_brujo.txt', 'w', encoding='utf-8') as f:
        f.write(mensaje.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', ''))
        
    enviar_mensaje_telegram(mensaje)

def ejecutar():
    file_name = 'historico_resultados.csv'
    if os.path.exists(file_name):
        df_historico = pd.read_csv(file_name, dtype={'numero': str})
        # AQUÍ ESTÁ LA LIMPIEZA DE FECHAS PARA QUE NO SE QUEDE CARGANDO 4 MINUTOS
        fechas_ya_descargadas = set(str(fecha).split(' ')[0] for fecha in df_historico['fecha'].unique())
    else:
        df_historico = pd.DataFrame(columns=['fecha', 'hora', 'nombre', 'numero'])
        fechas_ya_descargadas = set()

    nuevos_registros = []
    for i in range(366):
        fecha_evaluar = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        if i == 0 or fecha_evaluar not in fechas_ya_descargadas:
            datos_dia = extraer_datos_por_fecha(i)
            if datos_dia: nuevos_registros.extend(datos_dia)
            time.sleep(1)

    if nuevos_registros:
        verificar_y_notificar_bingo(df_historico, nuevos_registros)

        df_nuevos = pd.DataFrame(nuevos_registros)
        df_final = pd.concat([df_historico, df_nuevos])
        df_final['numero'] = df_final['numero'].apply(limpiar_formato_numero)
        df_final = df_final.drop_duplicates(subset=['fecha', 'hora', 'numero'])
        df_final['hora_temp'] = pd.to_datetime(df_final['hora'], format='%I:%M %p', errors='coerce').dt.time
        df_final = df_final.sort_values(by=['fecha', 'hora_temp'], ascending=[False, False]).drop(columns=['hora_temp'])
        df_final.to_csv(file_name, index=False)
        
        validar_teoria_pronostico(df_final)
    else:
        validar_teoria_pronostico(df_historico)

if __name__ == "__main__":
    ejecutar()
