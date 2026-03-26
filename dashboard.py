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

# Conexión directa a tu repositorio
TU_USUARIO_GITHUB = "Rayc3004"
TU_REPOSITORIO_GITHUB = "guacharito-pro-tracker"
URL_BASE_DATOS_RAW = f"https://raw.githubusercontent.com/{TU_USUARIO_GITHUB}/{TU_REPOSITORIO_GITHUB}/main/historico_resultados.csv"

# Diccionario maestro para mapeo número -> animalito
ANIMALITOS_MASTER = {str(i).zfill(2) if i not in [0, 00] else str(i): "NOMBRE" for i in range(100)} 

TABLA_BRUJO = [
    ("35", "86"), ("14", "96"), ("02", "46"), ("75", "56"), ("53", "39"), ("37", "52"), ("48", "67"), ("83", "59"), ("94", "91"), ("63", "70"), 
    ("76", "82"), ("50", "65"), ("81", "47"), ("78", "62"), ("89", "71"), ("0", "92"), ("28", "61"), ("09", "38"), ("26", "40"), ("30", "85"), 
    ("11", "69"), ("07", "43"), ("20", "58"), ("32", "41"), ("17", "88"), ("05", "55"), ("22", "72"), ("34", "49"), ("15", "68"), ("03", "98"), 
    ("24", "73"), ("36", "80"), ("13", "57"), ("01", "87"), ("00", "90"), ("27", "95"), ("10", "66"), ("25", "51"), ("29", "44"), ("12", "84"), 
    ("08", "93"), ("19", "64"), ("31", "42"), ("18", "54"), ("06", "74"), ("21", "97"), ("33", "77"), ("16", "60"), ("04", "45"), ("23", "79")
]

# Configuración de la pestaña del navegador
st.set_page_config(
    layout="wide", 
    page_title="El Brujo Guacharito - Pronósticos",
    page_icon="🔮"
)

# --- FUNCIONES TÉCNICAS ---

def limpiar_formato_numero(x):
    val = str(x).strip()
    if val.endswith('.0'): val = val[:-2]
    if val in ["0", "00"]: return val
    return val.zfill(2)

@st.cache_data(ttl=1800) 
def cargar_datos_raw():
    try:
        response = requests.get(URL_BASE_DATOS_RAW, timeout=15)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text), dtype={'numero': str})
        
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['numero'] = df['numero'].apply(limpiar_formato_numero)
        df['hora_dt'] = pd.to_datetime(df['hora'], format='%I:%M %p', errors='coerce').dt.time
        
        return df
    except Exception as e:
        st.error(f"Error cargando la base de datos. Asegúrate de que el repositorio sea público. Detalle: {e}")
        return pd.DataFrame()

def clasificar_semoforo(df):
    fecha_hoy = datetime.now()
    ultimas_salidas = df.groupby('numero')['fecha'].max()
    
    data_roja, data_amarilla, data_verde = [], [], []
    quemadas = 0   
    
    for p1, p2 in TABLA_BRUJO:
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
            
    df_roja = pd.DataFrame(data_roja) if data_roja else pd.DataFrame(columns=["Pareja", "Días Invicta"])
    df_amarilla = pd.DataFrame(data_amarilla) if data_amarilla else pd.DataFrame(columns=["Pareja", "Días Invicta"])
    df_verde = pd.DataFrame(data_verde) if data_verde else pd.DataFrame(columns=["Pareja", "Días Invicta"])

    return df_roja, df_amarilla, df_verde, quemadas

# ==========================================
# --- ESTRUCTURA VISUAL DE LA WEB ---
# ==========================================

st.title("🔮 El Brujo Guacharito - Pronósticos Exclusivos")
st.markdown(f"**Última actualización:** {datetime.now().strftime('%d-%m-%Y %I:%M %p')} | *Datos sincronizados en tiempo real*")

# --- 1. CARGA Y FILTROS ---
with st.spinner("Sincronizando con la base de datos del Brujo..."):
    df = cargar_datos_raw()

if df.empty:
    st.error("No se pudo cargar el historial de resultados.")
    st.stop()

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/186/186318.png", width=100) 
st.sidebar.header("Filtros de Análisis")
fecha_rango = st.sidebar.date_input(
    "Rango de Análisis Estadístico",
    [datetime.now() - timedelta(days=30), datetime.now()],
    min_value=df['fecha'].min().date() if not df.empty else datetime.now().date(),
    max_value=datetime.now().date()
)

# --- 2. EL SEMÁFORO DE PRONÓSTICOS ---
st.header("🎯 Semáforo Visual - Jugadas del Día")
st.markdown("Basado en el análisis matemático de las parejas invictas según la legendaria Tabla del Brujo.")

df_roja, df_amarilla, df_verde, quemadas = clasificar_semoforo(df)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎯 ALERTA ROJA")
    st.markdown("*Jugar Fuerte (+14 días invicta)*")
    if not df_roja.empty:
        st.markdown(df_roja.to_html(index=False, escape=False, classes='table table-striped'), unsafe_allow_html=True)
    else:
        st.success("Sin alertas rojas hoy.")

with col2:
    st.subheader("⚠️ ALERTA AMARILLA")
    st.markdown("*En Observación (7 a 14 días)*")
    if not df_amarilla.empty:
        st.markdown(df_amarilla.to_html(index=False, escape=False, classes='table table-striped'), unsafe_allow_html=True)
    else:
        st.info("Sin alertas amarillas.")

with col3:
    st.subheader("✅ ALERTA VERDE")
    st.markdown("*Frías - Recientes (1 a 6 días)*")
    if not df_verde.empty:
        st.markdown(df_verde.to_html(index=False, escape=False, classes='table table-striped'), unsafe_allow_html=True)
    else:
        st.info("Sin alertas verdes.")

st.markdown(f"**🔥 Parejas Quemadas (Descartadas para hoy):** {quemadas} de 50")
st.write("---")

# --- 3. ANÁLISIS ESTADÍSTICO INTERACTIVO ---
st.header("📈 Análisis Estadístico Interactivo")

# BLINDAJE DE SEGURIDAD PARA EL RANGO DE FECHAS
if len(fecha_rango) == 2:
    start_date, end_date = fecha_rango
    df_filtrado = df[
        (df['fecha'].dt.date >= start_date) &
        (df['fecha'].dt.date <= end_date)
    ]
else:
    st.warning("⏳ Por favor, selecciona una fecha de inicio y una de fin en el menú lateral para ver los gráficos.")
    df_filtrado = pd.DataFrame()

# A) Gráfico de Frecuencia de Animalitos
st.subheader("📊 Frecuencia de Animalitos (+ Salidores)")

if not df_filtrado.empty:
    # CORRECCIÓN: value_counts() en lugar de value_count()
    frecuencia_animal = df_filtrado['nombre'].value_counts().reset_index()
    frecuencia_animal.columns = ['Animalito', 'Veces que Salió']
    
    fig_frec = px.bar(
        frecuencia_animal.head(15), 
        x='Veces que Salió',
        y='Animalito',
        orientation='h',
        title=f"Top 15 Animalitos más Salidores",
        labels={'Animalito': 'Animalito', 'Veces que Salió': 'Sorteos'},
        template='plotly_white',
        color='Veces que Salió',
        color_continuous_scale='Viridis'
    )
    fig_frec.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_frec, use_container_width=True)
elif len(fecha_rango) == 2: # Solo muestra la alerta si hay 2 fechas seleccionadas pero no hay data
    st.info("No hay sorteos registrados en este rango de fechas.")

st.write("---")

# B) Frecuencia de Hora
st.subheader("⏰ Frecuencia por Horario de Sorteo")

if not df_filtrado.empty:
    frecuencia_hora = df_filtrado.groupby('hora')['numero'].count().reset_index()
    frecuencia_hora.columns = ['Hora Sorteo', 'Cantidad Sorteos']
    
    fig_hora = px.bar(
        frecuencia_hora,
        x='Cantidad Sorteos',
        y='Hora Sorteo',
        orientation='h',
        title="Volumen de Animalitos sorteados por Hora",
        labels={'Cantidad Sorteos': 'Sorteos Totales', 'Hora Sorteo': 'Horario'},
        template='plotly_white',
        color='Cantidad Sorteos', 
        color_continuous_scale='Reds' 
    )
    st.plotly_chart(fig_hora, use_container_width=True)

st.write("---")
st.markdown("<div style='text-align: center; color: gray;'><em>Automatizado por El Brujo Guacharito - 2026</em></div>", unsafe_allow_html=True)
