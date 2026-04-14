import rasterio
import numpy as np
import pandas as pd

arquivo = "output_SRTMGL1.tif"

with rasterio.open(arquivo) as src:
    banda = src.read(1)
    transform = src.transform

# Criar grid de índices
linhas, colunas = banda.shape
cols, rows = np.meshgrid(np.arange(colunas), np.arange(linhas))

# Converter para coordenadas reais
xs, ys = rasterio.transform.xy(transform, rows, cols)

xs = np.array(xs).flatten()
ys = np.array(ys).flatten()
zs = banda.flatten()

# Remover valores inválidos
mask = zs != src.nodata

df = pd.DataFrame({
    "X": xs[mask],
    "Y": ys[mask],
    "Z": zs[mask]
})

df.to_csv("topografia.csv", index=False)

print("CSV gerado com sucesso!")