import pandas as pd
from datetime import datetime
import os

TABLA_BRUJO = [
    ("35", "86"), ("14", "96"), ("02", "46"), ("75", "56"), ("53", "39"), ("37", "52"), ("48", "67"), ("83", "59"), ("94", "91"), ("63", "70"), 
    ("76", "82"), ("50", "65"), ("81", "47"), ("78", "62"), ("89", "71"), ("0", "92"), ("28", "61"), ("09", "38"), ("26", "40"), ("30", "85"), 
    ("11", "69"), ("07", "43"), ("20", "58"), ("32", "41"), ("17", "88"), ("05", "55"), ("22", "72"), ("34", "49"), ("15", "68"), ("03", "98"), 
    ("24", "73"), ("36", "80"), ("13", "57"), ("01", "87"), ("00", "90"), ("27", "95"), ("10", "66"), ("25", "51"), ("29", "44"), ("12", "84"), 
    ("08", "93"), ("19", "64"), ("31", "42"), ("18", "54"), ("06", "74"), ("21", "97"), ("33", "77"), ("16", "60"), ("04", "45"), ("23", "79")
]

def limpiar_formato_numero(x):
    val = str(x).strip()
    if val.endswith('.0'): val = val[:-2]
    if val in ["0", "00"]: return val
    return val.zfill(2)

def ejecutar_auditoria():
    print("Iniciando Auditoría Histórica (Backtesting)...")
    file_name = 'historico_resultados.csv'
    
    if not os.path.exists(file_name):
        print("No se encontró el archivo histórico. Abortando.")
        return

    # Leer datos y limpiar
    df = pd.read_csv(file_name, dtype={'numero': str})
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['numero'] = df['numero'].apply(limpiar_formato_numero)
    
    # Ordenar cronológicamente (del más antiguo al más nuevo)
    df = df.sort_values('fecha')
    
    alertas_generadas = 0
    aciertos_rapidos = 0 # Salió entre 1 y 3 días después de la alerta
    aciertos_medios = 0  # Salió entre 4 y 7 días después
    aciertos_lentos = 0  # Tardó más de 7 días en salir
    
    for p1, p2 in TABLA_BRUJO:
        # Filtrar solo los días donde salió esta pareja específica
        fechas_pareja = df[df['numero'].isin([p1, p2])]['fecha'].drop_duplicates().tolist()
        
        if len(fechas_pareja) < 2:
            continue # No hay suficiente historial para esta pareja aún

        # Medir la distancia en días entre cada vez que salió
        for i in range(1, len(fechas_pareja)):
            brecha_dias = (fechas_pareja[i] - fechas_pareja[i-1]).days
            
            # Si pasaron 15 días o más sin salir, significa que ENTRO en Alerta Roja
            if brecha_dias >= 15:
                alertas_generadas += 1
                
                # ¿Cuántos días extras tardó en salir desde que entró en alerta roja (día 14)?
                dias_espera = brecha_dias - 14
                
                if dias_espera <= 3:
                    aciertos_rapidos += 1
                elif dias_espera <= 7:
                    aciertos_medios += 1
                else:
                    aciertos_lentos += 1

    # Guardar los resultados en un archivo de texto
    with open('reporte_auditoria.txt', 'w', encoding='utf-8') as f:
        f.write("📊 REPORTE DE BACKTESTING: LA PRUEBA DE FUEGO 📊\n")
        f.write(f"Analizado el: {datetime.now().strftime('%d-%m-%Y')}\n")
        f.write("="*50 + "\n\n")
        
        if alertas_generadas == 0:
            f.write("⚠️ Aún no hay suficientes datos históricos para generar alertas rojas pasadas. Deja que el sistema recopile más días.\n")
        else:
            f.write(f"🔍 Total de 'Alertas Rojas' históricas detectadas: {alertas_generadas}\n\n")
            f.write("¿Cuánto tardaron en salir DESPUÉS de entrar en Alerta Roja?\n")
            f.write(f"🟢 Muy Rápido (1 a 3 días de espera): {aciertos_rapidos} veces ({(aciertos_rapidos/alertas_generadas)*100:.1f}%)\n")
            f.write(f"🟡 Normal (4 a 7 días de espera): {aciertos_medios} veces ({(aciertos_medios/alertas_generadas)*100:.1f}%)\n")
            f.write(f"🔴 Lento (Más de 7 días de espera): {aciertos_lentos} veces ({(aciertos_lentos/alertas_generadas)*100:.1f}%)\n\n")
            
            f.write("--- CONCLUSIÓN DEL SISTEMA ---\n")
            if (aciertos_rapidos + aciertos_medios) > (alertas_generadas / 2):
                f.write("✅ ESTRATEGIA SÓLIDA: Más del 50% de las alertas rojas salen en la primera semana. Es rentable usar la técnica de 'perseguir' el número subiendo la apuesta.\n")
            else:
                f.write("⚠️ ESTRATEGIA DE RIESGO: Muchas alertas tardan más de una semana en salir. Se sugiere cambiar el umbral de la Alerta Roja a 20 días para mayor seguridad financiera.\n")

if __name__ == '__main__':
    ejecutar_auditoria()
