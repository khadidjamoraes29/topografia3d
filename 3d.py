import streamlit as st
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🌍 Sistema de Visualização Topográfica 3D")

# -------------------------
# Upload de arquivo
# -------------------------
uploaded_file = st.file_uploader("Envie um arquivo CSV com colunas X,Y,Z", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file)
    x = data.iloc[:, 0]
    y = data.iloc[:, 1]
    z = data.iloc[:, 2]
else:
    st.warning("Nenhum arquivo enviado. Usando dados de exemplo.")

    np.random.seed(0)
    n = 200
    x = np.random.uniform(0, 10, n)
    y = np.random.uniform(0, 10, n)
    z = np.sin(x) * np.cos(y) * 10

# -------------------------
# Sidebar (controles)
# -------------------------
st.sidebar.header("⚙️ Configurações")

resolucao = st.sidebar.slider("Resolução da malha", 50, 200, 120)
tipo_interp = st.sidebar.selectbox("Interpolação", ["cubic", "linear", "nearest"])
mostrar_contorno = st.sidebar.checkbox("Curvas de nível", True)

usar_degrau = st.sidebar.checkbox("Efeito camadas (mineração)", True)
niveis = st.sidebar.slider("Quantidade de níveis", 5, 30, 15)

cor = st.sidebar.selectbox("Paleta de cores", ["Turbo", "Jet", "Viridis"])

# -------------------------
# Interpolação
# -------------------------
grid_x, grid_y = np.meshgrid(
    np.linspace(min(x), max(x), resolucao),
    np.linspace(min(y), max(y), resolucao)
)

grid_z = griddata((x, y), z, (grid_x, grid_y), method=tipo_interp)

# Remover valores NaN
grid_z = np.nan_to_num(grid_z, nan=np.nanmean(grid_z))

# -------------------------
# Efeito de "degrau"
# -------------------------
if usar_degrau:
    levels = np.linspace(np.min(grid_z), np.max(grid_z), niveis)
    grid_z = np.digitize(grid_z, levels)

# -------------------------
# Gráfico 3D
# -------------------------
fig = go.Figure()

fig.add_trace(go.Surface(
    x=grid_x,
    y=grid_y,
    z=grid_z,
    colorscale=cor,
    showscale=True,

    lighting=dict(
        ambient=0.4,
        diffuse=0.9,
        roughness=0.8,
        specular=0.3
    ),

    lightposition=dict(
        x=100,
        y=200,
        z=100
    ),

    contours={
        "z": {
            "show": mostrar_contorno,
            "usecolormap": True,
            "highlightcolor": "black",
            "project_z": True
        }
    }
))

# -------------------------
# Layout (visual profissional)
# -------------------------
fig.update_layout(
    scene=dict(
        xaxis_visible=False,
        yaxis_visible=False,
        zaxis_title='Altitude',

        camera=dict(
            eye=dict(x=1.8, y=1.8, z=1.2)
        )
    ),

    paper_bgcolor='black',
    plot_bgcolor='black',
    margin=dict(l=0, r=0, t=40, b=0)
)

# -------------------------
# Exibir
# -------------------------
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Exportar
# -------------------------
if st.button("📥 Exportar como HTML"):
    fig.write_html("mapa_3d.html")
    with open("mapa_3d.html", "rb") as f:
        st.download_button("Baixar mapa", f, file_name="mapa_3d.html")