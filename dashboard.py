
import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Configuracion
st.set_page_config(page_title="Dashboard Proyectos Ecuador", layout="wide")
st.title("📊 Dashboard de Proyectos - Ecuador")

# Cargar datos
@st.cache_data
def cargar_datos():
    df = pd.read_excel("Planificacion_resumen_GCC_2025jun25.xlsx", sheet_name="Resumen 2025")
    def limpiar_provincias(provincia_texto):
        import re
        if not isinstance(provincia_texto, str):
            return []
        correcciones = {
            "Manbí": "Manabí",
            "Manabi": "Manabí",
            "convincias": "provincias",
            "convinciad": "provincias"
        }
        for incorrecto, correcto in correcciones.items():
            provincia_texto = provincia_texto.replace(incorrecto, correcto)
        if "24 provincias" in provincia_texto or "provincias" in provincia_texto:
            return ["TODAS"]
        if "7 provincias de la costa" in provincia_texto:
            costa = ["Esmeraldas", "Manabí", "Santo Domingo", "Los Ríos", "Guayas", "Santa Elena", "El Oro"]
            return costa + (["Loja"] if "Loja" in provincia_texto else [])
        if "Amazonia" in provincia_texto:
            return ["Sucumbíos", "Napo", "Orellana", "Pastaza", "Morona Santiago", "Zamora Chinchipe"]
        provincias = re.split(r",|\sy\s", provincia_texto)
        return [p.strip() for p in provincias if p.strip()]
    df["Provincias"] = df["Provincia_mapa"].apply(limpiar_provincias)
    return df

df = cargar_datos()

# Sidebar filtros
st.sidebar.header("Filtros")
fase = st.sidebar.multiselect("Fase del proyecto", df["Fase"].dropna().unique())
entidades = st.sidebar.multiselect("Entidad que lidera", df["Entidad que lidera"].dropna().unique())
prov_filtro = st.sidebar.multiselect("Provincia involucrada", sorted({p for provs in df["Provincias"] for p in provs if p != "TODAS"}))

# Filtrar datos
def aplicar_filtros(df):
    df_filtrado = df.copy()
    if fase:
        df_filtrado = df_filtrado[df_filtrado["Fase"].isin(fase)]
    if entidades:
        df_filtrado = df_filtrado[df_filtrado["Entidad que lidera"].isin(entidades)]
    if prov_filtro:
        df_filtrado = df_filtrado[df_filtrado["Provincias"].apply(lambda x: any(p in x for p in prov_filtro))]
    return df_filtrado

df_filtrado = aplicar_filtros(df)

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("📁 Total Proyectos", len(df_filtrado))
col2.metric("✅ Avance Promedio", f"{df_filtrado['Porcentaje de avance aprox.'].astype(float).mean():.0%}")
col3.metric("💰 Proyectos con presupuesto", df_filtrado['Monto requerido (USD)'].apply(lambda x: str(x).replace("?", "")).astype(str).str.isnumeric().sum())

# Gráficos
col4, col5 = st.columns(2)
with col4:
    fig1 = px.histogram(df_filtrado, x="Entidad que lidera", title="Proyectos por Entidad", color_discrete_sequence=["#0072B2"])
    st.plotly_chart(fig1, use_container_width=True)

with col5:
    fig2 = px.pie(df_filtrado, names="Fase", title="Distribución por Fase", color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig2, use_container_width=True)

# Mapa
st.subheader("🗺️ Mapa de Provincias involucradas")

@st.cache_data
def cargar_mapa_ecuador():
    url = "https://raw.githubusercontent.com/juaneladio/geojson-ecuador/master/ecuador_provincias.geojson"
    return gpd.read_file(url)

gdf_provincias = cargar_mapa_ecuador()

# Marcar provincias
provincias_seleccionadas = set()
for provs in df_filtrado["Provincias"]:
    provincias_seleccionadas.update(provs)

m = folium.Map(location=[-1.5, -78.0], zoom_start=6)

for _, row in gdf_provincias.iterrows():
    nombre = row["DPA_DESPRO"]
    color = "#3186cc" if nombre in provincias_seleccionadas or "TODAS" in provincias_seleccionadas else "#dddddd"
    folium.GeoJson(
        row["geometry"],
        name=nombre,
        style_function=lambda x, col=color: {"fillColor": col, "color": "black", "weight": 1, "fillOpacity": 0.6},
        tooltip=nombre
    ).add_to(m)

st_data = st_folium(m, width=700, height=500)

st.caption("© Dashboard generado con Streamlit. Datos: UGCC-DRAA")
