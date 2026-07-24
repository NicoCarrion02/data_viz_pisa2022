import streamlit as st
import plotly.express as px
import pandas as pd
from etl import procesar_datos_completos, calcular_resumen_macro

# 1. Configuración adaptativa
st.set_page_config(page_title="PISA 2022: Análisis de Brechas", page_icon="📊", layout="wide")

@st.cache_data
def cargar_todo():
    df_micro = procesar_datos_completos("data/pisa2022.parquet")
    df_macro = calcular_resumen_macro(df_micro).reset_index(drop=True)
    return df_micro, df_macro

df_micro, df_macro = cargar_todo()
paises_disponibles = sorted(df_macro["CNT"].unique())

# ==========================================
# 2. MOTOR DE SINCRONIZACIÓN Y SELECCIÓN MÚLTIPLE
# ==========================================
# Inicializamos las memorias del estado
for key in ["activos", "last_map", "last_bar", "last_ms"]:
    if key not in st.session_state:
        st.session_state[key] = []

def procesar_clic_acumulativo(incoming, last_raw, activos_actuales):
    """Lógica que permite agregar o quitar países con un solo clic sin borrar los anteriores."""
    nuevos_activos = activos_actuales.copy()
    
    if len(incoming) == 1:
        # Si se hizo un clic normal, evaluamos si ya estaba para agregarlo o quitarlo
        pais_clickeado = incoming[0]
        if pais_clickeado in nuevos_activos:
            nuevos_activos.remove(pais_clickeado)
        else:
            nuevos_activos.append(pais_clickeado)
    elif len(incoming) == 0 and len(last_raw) == 1:
        # Plotly envía una lista vacía cuando vuelves a hacer clic exactamente en el último punto (Deselección nativa)
        if last_raw[0] in nuevos_activos:
            nuevos_activos.remove(last_raw[0])
    elif len(incoming) > 1:
        # Si el usuario selecciona varios de golpe (con Shift o Lazo)
        for pais in incoming:
            if pais not in nuevos_activos:
                nuevos_activos.append(pais)
                
    return nuevos_activos

# A. Leer qué está seleccionado directamente desde los gráficos y el filtro
curr_map = []
if "map_chart" in st.session_state and st.session_state.map_chart:
    curr_map = [p["location"] for p in st.session_state.map_chart.get("selection", {}).get("points", [])]

curr_bar = []
if "bar_chart" in st.session_state and st.session_state.bar_chart:
    curr_bar = [p["y"] for p in st.session_state.bar_chart.get("selection", {}).get("points", [])]

curr_ms = st.session_state.get("filtro_paises_widget", [])

# B. Detectar exactamente qué interfaz usó el usuario y actualizar todo
if curr_map != st.session_state.last_map:
    st.session_state.activos = procesar_clic_acumulativo(curr_map, st.session_state.last_map, st.session_state.activos)
    st.session_state.last_map = curr_map
    st.session_state.last_ms = st.session_state.activos.copy() # Sincroniza filtro
    
elif curr_bar != st.session_state.last_bar:
    st.session_state.activos = procesar_clic_acumulativo(curr_bar, st.session_state.last_bar, st.session_state.activos)
    st.session_state.last_bar = curr_bar
    st.session_state.last_ms = st.session_state.activos.copy()

elif curr_ms != st.session_state.last_ms:
    st.session_state.activos = curr_ms.copy()
    st.session_state.last_ms = curr_ms.copy()

# C. Forzar al filtro lateral a mostrar la verdad absoluta
st.session_state.filtro_paises_widget = st.session_state.activos
activos = st.session_state.activos
hay_seleccion = len(activos) > 0


# ==========================================
# 3. BARRA LATERAL: Controles y Filtros
# ==========================================
with st.sidebar:
    st.header("⚙️ Parámetros")
    
    materia = st.selectbox("1. Materia a evaluar:", ["Matemáticas", "Lectura", "Ciencias"])
    col_promedio = f"{materia}_Avg" if materia != "Matemáticas" else "Matematicas_Avg"
    
    dimension = st.selectbox(
        "2. Dimensión de desigualdad:",
        options=["Nivel_Socioeconomico", "Genero"],
        format_func=lambda x: "Nivel Socioeconómico" if x == "Nivel_Socioeconomico" else "Brecha de Género"
    )

    n_paises = st.number_input(
        "3. Países top en el ranking:",
        min_value=5, max_value=len(paises_disponibles), value=15, step=5
    )
    
    st.divider()
    st.subheader("Filtro Global Sincronizado")
    
    st.multiselect(
        "Países activos en el análisis:",
        options=paises_disponibles,
        key="filtro_paises_widget"
    )
    
    if st.button("🔄 Limpiar Selección", use_container_width=True):
        st.session_state.activos = []
        st.session_state.last_map = []
        st.session_state.last_bar = []
        st.session_state.last_ms = []
        st.session_state.filtro_paises_widget = []
        st.rerun()

# ==========================================
# 4. CABECERA PRINCIPAL
# ==========================================
st.title("🌍 Desempeño y Brechas Educativas en PISA 2022")
st.markdown(f"Rendimiento global en **{materia}** y exploración de desigualdades estructurales.")

col_mapa, col_rank = st.columns([1.5, 1])

# --- PANEL 1: MAPA GLOBAL ---
with col_mapa:
    fig_mapa = px.choropleth(
        df_macro, locations="CNT", color=col_promedio, hover_name="CNT",
        color_continuous_scale="Viridis", labels={col_promedio: f"Puntaje"}
    )
    fig_mapa.update_traces(hovertemplate="<b>%{hovertext}</b><br>Promedio: %{z:.1f}<extra></extra>")
    
    if hay_seleccion:
        indices_mapa = df_macro.index[df_macro['CNT'].isin(activos)].tolist()
        fig_mapa.update_traces(selectedpoints=indices_mapa)

    fig_mapa.update_layout(
        geo=dict(showframe=False, showcoastlines=True, bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        clickmode="event+select"
    )
    
    st.plotly_chart(fig_mapa, use_container_width=True, theme="streamlit", on_select="rerun", key="map_chart")

# --- PANEL 2: RANKING DIRECTO ---
with col_rank:
    df_top = df_macro.sort_values(by=col_promedio, ascending=False).head(n_paises)
    if hay_seleccion:
        df_extra = df_macro[df_macro["CNT"].isin(activos)]
        df_top = pd.concat([df_top, df_extra]).drop_duplicates(subset=["CNT"])
    
    df_top = df_top.sort_values(by=col_promedio, ascending=True).reset_index(drop=True)
    
    fig_bar = px.bar(
        df_top, x=col_promedio, y="CNT", orientation="h",
        color_discrete_sequence=["#3B82F6"]
    )
    
    if hay_seleccion:
        indices_barra = df_top.index[df_top['CNT'].isin(activos)].tolist()
        fig_bar.update_traces(selectedpoints=indices_barra)

    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(title=f"Puntaje"), yaxis=dict(title=""), clickmode="event+select"
    )
    
    st.plotly_chart(fig_bar, use_container_width=True, theme="streamlit", on_select="rerun", key="bar_chart")

st.divider()

# ==========================================
# 5. SECCIÓN INFERIOR: Vista Micro y KPIs
# ==========================================
global_avg = df_macro[col_promedio].mean()
global_anx = df_macro["Ansiedad_Avg"].mean()
global_muestra = df_macro["Muestra_Estudiantes"].sum()

if hay_seleccion:
    df_analisis = df_micro[df_micro["CNT"].isin(activos)]
    macro_activos = df_macro[df_macro["CNT"].isin(activos)]
    
    val_promedio = macro_activos[col_promedio].mean()
    val_ansiedad = macro_activos["Ansiedad_Avg"].mean()
    val_muestra = macro_activos["Muestra_Estudiantes"].sum()
    
    # Lógica dinámica del título
    n_sel = len(activos)
    if n_sel == 1:
        titulo = f"🔍 Análisis Detallado: {activos[0]}"
    elif n_sel <= 5:
        titulo = f"🔍 Análisis Detallado: {', '.join(activos)}"
    else:
        titulo = f"🔍 Análisis Detallado: {n_sel} países seleccionados"
        
    st.subheader(titulo)
    k1, k2, k3 = st.columns(3)
    # Solo mostramos el vs Mundo cuando hay una selección activa
    k1.metric(f"Promedio {materia}", f"{val_promedio:.1f}", f"{val_promedio - global_avg:.1f} vs Mundo")
    k2.metric("Índice de Ansiedad", f"{val_ansiedad:.2f}", f"{val_ansiedad - global_anx:.2f} vs Mundo", delta_color="inverse")
    k3.metric("Muestra Evaluada", f"{val_muestra:,} estudiantes")
else:
    df_analisis = df_micro.sample(n=min(len(df_micro), 15000), random_state=42)
    st.subheader("🌐 Análisis Global (Haz clic en países o búscalo en el filtro para desglosarlo)")
    
    k1, k2, k3 = st.columns(3)
    k1.metric(f"Promedio Global {materia}", f"{global_avg:.1f}")
    k2.metric("Índice de Ansiedad Global", f"{global_anx:.2f}")
    k3.metric("Muestra Total Evaluada", f"{global_muestra:,} estudiantes")

# --- Gráfico Inferior de Brechas (Boxplot) ---
if dimension == "Nivel_Socioeconomico":
    orden = ["Q1 (Bajo)", "Q2", "Q3", "Q4 (Alto)"]
else:
    orden = ["Femenino", "Masculino"]

fig_box = px.box(
    df_analisis, x=dimension, y=materia, color=dimension,
    category_orders={dimension: orden},
    title=f"Distribución de puntajes por {dimension.replace('_', ' ')}"
)

fig_box.update_layout(
    showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(title=""), yaxis=dict(title=f"Puntaje ({materia})")
)

st.plotly_chart(fig_box, use_container_width=True, theme="streamlit")