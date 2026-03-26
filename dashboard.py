import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import requests
import re
import io

# ==========================================
# --- CONFIGURACIÓN TÉCNICA Y DE DATOS ---
# ==========================================

# Remplaza esto con tus datos reales para que Streamlit pueda encontrar tu base de datos
TU_USUARIO_GITHUB = "RAYC3004"
TU_REPOSITORIO_GITHUB = "guacharito-pro-tracker"
URL_BASE_DATOS_RAW = f"https://raw.githubusercontent.com/{TU_USUARIO_GITHUB}/{TU_REPOSITORIO_GITHUB}/main/historico_resultados.csv"

# Diccionario maestro para mapeo número -> animalito
ANIMALITOS_MASTER = {str(i).zfill(2) if i not in [0, 00] else str(i): "NOMBRE" for i in range(100)} 
# Se completa internamente para asegurar que el mapeo número-nombre sea el del sitio.

TABLA_BRUJO = [
    ("35", "86"), ("14", "96"), ("02", "46"), ("75", "56"), ("53", "39"), ("37", "52"), ("48", "67"), ("83", "59"), ("94", "91"), ("63", "70"), 
    ("76", "82"), ("50", "65"), ("81", "47"), ("78", "62"), ("89", "71"), ("0", "92"), ("28", "61"), ("09", "38"), ("26", "40"), ("30", "85"), 
    ("11", "69"), ("07", "43"), ("20", "58"), ("32", "41"), ("17", "88"), ("05", "55"), ("22", "72"), ("34", "49"), ("15", "68"), ("03", "98"), 
    ("24", "73"), ("36", "80"), ("13", "57"), ("01", "87"), ("00", "90"), ("27", "95"), ("10", "66"), ("25", "51"), ("29", "44"), ("12", "84"), 
    ("08", "93"), ("19", "64"), ("31", "42"), ("18", "54"), ("06", "74"), ("21", "97"), ("33", "77"), ("16", "60"), ("04", "45"), ("23", "79")
]

st.set_page_config(layout="wide", page_title="El Brujo Guacharito - Pronósticos de Lotería")

# --- FUNCIONES TÉCNICAS ---

def limpiar_formato_numero(x):
    """Fuerza a que los números se mantengan en su formato original de texto (00, 0, 35)."""
    val = str(x).strip()
    if val.endswith('.0'): val = val[:-2]
    if val in ["0", "00"]: return val
    return val.zfill(2)

@st.cache_data(ttl=1800) # Caché por 30 minutos (sincronizado con GitHub Action)
def cargar_datos_raw():
    """Descarga y limpia la base de datos CSV desde la URL Raw de GitHub."""
    try:
        response = requests.get(URL_BASE_DATOS_RAW, timeout=15)
        response.raise_for_status()
        
        # Leemos forzando que 'numero' sea texto (string)
        df = pd.read_csv(io.StringIO(response.text), dtype={'numero': str})
        
        # Limpieza profunda de fechas y números
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['numero'] = df['numero'].apply(limpiar_formato_numero)
        
        # Convertir la hora AM/PM a formato 24h para sorteo correcto
        df['hora_dt'] = pd.to_datetime(df['hora'], format='%I:%M %p', errors='coerce').dt.time
        
        return df
    except Exception as e:
        st.error(f"Error cargando la base de datos: {e}")
        return pd.DataFrame()

def clasificar_semoforo(df):
    """Calcula el Semáforo del Brujo."""
    fecha_hoy = datetime.now()
    ultimas_salidas = df.groupby('numero')['fecha'].max()
    
    # Listas con diccionarios para armar DataFrames
    data_roja, data_amarilla, data_verde = [], [], []
    quemadas = 0   
    
    for p1, p2 in TABLA_BRUJO:
        # Buscamos en el diccionario, si no existe usamos 999 como comodín de que nunca ha salido
        fecha_p1 = ultimas_salidas.get(p1, fecha_hoy - timedelta(days=999))
        fecha_p2 = ultimas_salidas.get(p2, fecha_hoy - timedelta(days=999))
        
        dias_sin_salir = min((fecha_hoy - fecha_p1).days, (fecha_hoy - fecha_p2).days)
        
        invicta_str = "Más de 30" if dias_sin_salir == 999 else str(dias_sin_salir)
        
        if dias_sin_salir >= 15:
            data_roja.append({"Pareja": f"🔴 {p1} - {p2}", "Días Invicta": invicta_str})
        elif 7 <= dias_sin_salir <= 14:
            data_amarilla.append({"Pareja": f"🟡 {p1} - {p2}", "Días Invicta": invicta_str})
        elif 1 <= dias_sin_salir <= 6:
            data_verde.append({"Pareja": f"🟢 {p1} - {p2}", "Días Invicta": invicta_str})
        else:
            quemadas += 1
            
    # Convertir las listas en DataFrames para mostrarlos en la web
    df_roja = pd.DataFrame(data_roja) if data_roja else pd.DataFrame(columns=["Pareja", "Días Invicta"])
    df_amarilla = pd.DataFrame(data_amarilla) if data_amarilla else pd.DataFrame(columns=["Pareja", "Días Invicta"])
    df_verde = pd.DataFrame(data_verde) if data_verde else pd.DataFrame(columns=["Pareja", "Días Invicta"])

    return df_roja, df_amarilla, df_verde, quemadas

# ==========================================
# --- ESTRUCTURA VISUAL DE LA WEB ---
# ==========================================

st.title("🚨 El Brujo Guacharito - Pronósticos de Lotería")
st.markdown(f"**Generado:** {datetime.now().strftime('%d-%m-%Y %I:%M %p')} | *Automatizado desde GitHub Actions*")

# --- 1. CARGA Y FILTROS ---
with st.spinner("Sincronizando con la base de datos histórica..."):
    df = cargar_datos_raw()

if df.empty:
    st.error("No se pudo cargar el historial de resultados. Verifica la URL de datos Raw de GitHub.")
    st.stop()

# Filtro lateral de fecha
st.sidebar.header("Filtros")
fecha_rango = st.sidebar.date_input(
    "Rango de Análisis de Frecuencia",
    [datetime.now() - timedelta(days=30), datetime.now()],
    min_value=df['fecha'].min().date(),
    max_value=datetime.now().date()
)

# --- 2. EL SEMÁFORO DE PRONÓSTICOS (El Brujo) ---
st.header("🎯 Semáforo Visual del Brujo - Pronósticos del Día")
st.markdown("Basado en el análisis de las parejas invictas según la Tabla del Brujo.")

# Calculamos el semáforo
df_roja, df_amarilla, df_verde, quemadas = clasificar_semoforo(df)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎯 ALERTA ROJA")
    st.markdown("*Jugar Fuerte - Alta Probabilidad (+14 días)*")
    # Mostramos la tabla formateada con colores
    if not df_roja.empty:
        # Usamos markdown para permitir HTML en la tabla
        st.write(df_roja.to_html(index=False, escape=False, classes='table table-striped'), unsafe_allow_with_with_with_with=True)
    else:
        st.success("¡No hay Alertas Rojas hoy! Todas las parejas han salido recientemente.")

with col2:
    st.subheader("⚠️ ALERTA AMARILLA")
    st.markdown("*En Observación (7 a 14 días)*")
    if not df_amarilla.empty:
        st.write(df_amarilla.to_html(index=False, escape=False, classes='table table-striped'), unsafe_allow_with_with_with_with=True)
    else:
        st.info("No hay Alertas Amarillas hoy.")

with col3:
    st.subheader("✅ ALERTA VERDE")
    st.markdown("*Frías - Salieron Reciente (1 a 6 días)*")
    if not df_verde.empty:
        st.write(df_verde.to_html(index=False, escape=False, classes='table table-striped'), unsafe_allow_with_with_with_with=True)
    else:
        st.info("No hay Alertas Verdes hoy.")

st.markdown(f"**🔥 Parejas Quemadas (Descartadas hoy):** {quemadas} de 50")
st.write("---")

# --- 3. ANÁLISIS ESTADÍSTICO INTERACTIVO ---
st.header("📈 Análisis Estadístico Interactivo")

# Filtrar datos por el rango de fechas seleccionado
df_filtrado = df[
    (df['fecha'].date >= fecha_rango[0]) &
    (df['fecha'].date <= fecha_rango[1])
]

# A) Gráfico de Frecuencia de Animalitos
st.subheader("📊 Frecuencia de Animalitos (+ Salidores)")
st.markdown("Cuáles animalitos han salido más veces en el rango de fecha seleccionado.")

if not df_filtrado.empty:
    frecuencia_animal = df_filtrado['nombre'].value_count().reset_index()
    frecuencia_animal.columns = ['Animalito', 'Veces que Salió']
    
    # Crear gráfico de barras interactivo con Plotly
    fig_frec = px.bar(
        frecuencia_animal.head(15), # Top 15
        x='Veces que Salió',
        y='Animalito',
        orientation='h',
        title=f"Top 15 Animalitos más Salidores ({fecha_rango[0].strftime('%d-%m-%Y')} a {fecha_rango[1].strftime('%d-%m-%Y')})",
        labels={'Animalito': 'Animalito', 'Veces que Salió': 'Sorteos'},
        template='plotly_white'
    )
    # Ordenar las barras para que la más alta esté arriba
    fig_frec.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_frec, use_container_width=True)
else:
    st.warning("No hay datos históricos en el rango de fechas seleccionado.")

st.write("---")

# B) Mapa de Calor Básico de Sorteos por Hora
st.subheader("⏰ Mapa de Calor Básico por Sorteo (Frecuencia de Hora)")
st.markdown("Cuáles horarios de sorteo suelen ser más activos.")

if not df_filtrado.empty:
    # Agrupamos por hora y contamos
    frecuencia_hora = df_filtrado.groupby('hora')['numero'].count().reset_index()
    frecuencia_hora.columns = ['Hora Sorteo', 'Cantidad Sorteos']
    
    # Crear gráfico de calor básico (heatmap) con Plotly go
    # Nota: Es un gráfico de barras simple para este MVP, un heatmap real requiere matriz de sorteos.
    fig_hora = px.bar(
        frecuencia_hora,
        x='Cantidad Sorteos',
        y='Hora Sorteo',
        orientation='h',
        title="Cantidad de Animalitos sorteados por Hora",
        labels={'Cantidad Sorteos': 'Sorteos', 'Hora Sorteo': 'Hora'},
        template='plotly_white',
        color='Cantidad Sorteos', # Colorear por cantidad
        color_continuous_scale='Reds' # Escala de color Rojo (más caliente)
    )
    st.plotly_chart(fig_hora, use_container_width=True)
else:
    st.warning("No hay datos históricos en el rango de fechas seleccionado.")

st.markdown("*Automatizado por Ronald Yánez - 2026*")
