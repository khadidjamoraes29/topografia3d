import streamlit as st
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
import plotly.graph_objects as go
from pyproj import Transformer
import richdem as rd

st.set_page_config(layout="wide")

st.title("🌍 Sistema de Engenharia Topográfica 3D")

# -------------------------
# Upload
# -------------------------
uploaded_file = st.file_uploader("Envie CSV (X,Y,Z)", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file)

    lon = data.iloc[:, 0].values
    lat = data.iloc[:, 1].values
    z = data.iloc[:, 2].values

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32725", always_xy=True)
    x, y = transformer.transform(lon, lat)

    x = x - np.min(x)
    y = y - np.min(y)

else:
    st.warning("Usando dados de exemplo")
    np.random.seed(0)
    n = 200
    x = np.random.uniform(0, 100, n)
    y = np.random.uniform(0, 100, n)
    z = np.sin(x / 10) * np.cos(y / 10) * 10

# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("⚙️ Configurações")

resolucao = st.sidebar.slider("Resolução", 50, 200, 120)

modo = st.sidebar.selectbox(
    "Modo de análise",
    ["Visualização 3D", "Inclinação", "Drenagem", "Terraplanagem"]
)

mostrar_pontos = st.sidebar.checkbox("Mostrar pontos originais", False)

st.sidebar.header("🏗️ Engenharia")

limite_rampa = st.sidebar.slider("Inclinação máxima (%)", 5.0, 20.0, 8.33)
nivel_plano = st.sidebar.slider(
    "Cota de nivelamento",
    float(np.min(z)), float(np.max(z)), float(np.mean(z))
)

# Drenagem
st.sidebar.header("💧 Drenagem")
suavizar = st.sidebar.checkbox("Suavizar terreno", True)
sigma = st.sidebar.slider("Intensidade suavização", 0.5, 3.0, 1.0)
threshold_rios = st.sidebar.slider("Threshold rios", 10, 1000, 200)

# -------------------------
# Interpolação ROBUSTA
# -------------------------
grid_x, grid_y = np.meshgrid(
    np.linspace(min(x), max(x), resolucao),
    np.linspace(min(y), max(y), resolucao)
)

# linear + fallback nearest (evita distorção)
grid_z = griddata((x, y), z, (grid_x, grid_y), method='linear')
grid_z_nearest = griddata((x, y), z, (grid_x, grid_y), method='nearest')
grid_z[np.isnan(grid_z)] = grid_z_nearest[np.isnan(grid_z)]

# -------------------------
# SEPARAÇÃO CORRETA DO TERRENO
# -------------------------
grid_z_original = grid_z.copy()

if suavizar:
    grid_z_suave = gaussian_filter(grid_z, sigma=sigma)
else:
    grid_z_suave = grid_z.copy()

# -------------------------
# ENGENHARIA
# -------------------------
dx = (np.max(x) - np.min(x)) / (resolucao - 1)
dy = (np.max(y) - np.min(y)) / (resolucao - 1)

# Inclinação (USA ORIGINAL)
dz_dx, dz_dy = np.gradient(grid_z_original, dx, dy)
slope = np.sqrt(dz_dx**2 + dz_dy**2)
slope_percent = slope * 100
areas_criticas = slope_percent > limite_rampa

# -------------------------
# DRENAGEM (USA SUAVIZADO)
# -------------------------
dem = rd.rdarray(grid_z_suave, no_data=-9999)

rd.FillDepressions(dem, in_place=True)
rd.ResolveFlats(dem, in_place=True)

flow_acc = rd.FlowAccumulation(dem, method='D8')
flow_acc = np.array(flow_acc)

rios = flow_acc > threshold_rios

# -------------------------
# Corte/Aterro (USA ORIGINAL)
# -------------------------
corte = np.where(grid_z_original > nivel_plano, grid_z_original - nivel_plano, 0)
aterro = np.where(grid_z_original < nivel_plano, nivel_plano - grid_z_original, 0)

volume_corte = np.sum(corte)
volume_aterro = np.sum(aterro)

# -------------------------
# Plot
# -------------------------
fig = go.Figure()

if mostrar_pontos:
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(size=2, color='white')
    ))

# 📐 INCLINAÇÃO
if modo == "Inclinação":

    mapa = np.where(slope_percent <= limite_rampa, 0, 1)

    fig.add_trace(go.Surface(
        x=grid_x,
        y=grid_y,
        z=grid_z_original,
        surfacecolor=mapa,
        colorscale=[[0, "green"], [1, "red"]],
        showscale=False
    ))

# 💧 DRENAGEM
elif modo == "Drenagem":

    fig.add_trace(go.Surface(
        x=grid_x,
        y=grid_y,
        z=grid_z_original,
        surfacecolor=np.log1p(flow_acc),
        colorscale="Blues",
        showscale=True
    ))

    fig.add_trace(go.Surface(
        x=grid_x,
        y=grid_y,
        z=grid_z_original + 0.1,
        surfacecolor=rios.astype(int),
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "red"]],
        showscale=False
    ))

# 🏗️ TERRAPLANAGEM
elif modo == "Terraplanagem":

    mapa = np.zeros_like(grid_z_original)
    mapa[grid_z_original > nivel_plano] = 1
    mapa[grid_z_original < nivel_plano] = -1

    fig.add_trace(go.Surface(
        x=grid_x,
        y=grid_y,
        z=grid_z_original,
        surfacecolor=mapa,
        colorscale=[
            [0.0, "blue"],
            [0.5, "green"],
            [1.0, "red"]
        ],
        cmin=-1,
        cmax=1,
        showscale=False
    ))

# 🌍 VISUAL
else:
    fig.add_trace(go.Surface(
        x=grid_x,
        y=grid_y,
        z=grid_z_original,
        colorscale="Turbo",
        showscale=True
    ))

fig.update_layout(
    scene=dict(
        xaxis_visible=False,
        yaxis_visible=False,
        zaxis_title='Altitude',
        camera=dict(eye=dict(x=1.8, y=1.8, z=1.2))
    ),
    paper_bgcolor='black',
    plot_bgcolor='black',
    margin=dict(l=0, r=0, t=40, b=0)
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# RESULTADOS
# -------------------------
st.subheader("📊 Diagnóstico do Terreno")

col1, col2, col3 = st.columns(3)

col1.metric("Volume Corte", f"{volume_corte:.2f}")
col2.metric("Volume Aterro", f"{volume_aterro:.2f}")
col3.metric(
    "Áreas Críticas (%)",
    f"{(np.sum(areas_criticas)/areas_criticas.size)*100:.1f}%"
)

st.metric("Células de drenagem (rios)", int(np.sum(rios)))

# -------------------------
# Exportar
# -------------------------
if st.button("📥 Exportar HTML"):
    fig.write_html("mapa_3d.html")
    with open("mapa_3d.html", "rb") as f:
        st.download_button("Baixar", f, file_name="mapa_3d.html")