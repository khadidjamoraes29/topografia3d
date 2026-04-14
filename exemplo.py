import numpy as np
import pandas as pd

def gerar_terreno_avancado(n=200):
    X, Y = np.meshgrid(np.linspace(0, 50, n), np.linspace(0, 50, n))

    Z = np.zeros_like(X)

    # várias frequências (fractal)
    for i in range(1, 6):
        Z += (1/i) * np.sin(X * i / 3) * np.cos(Y * i / 3)

    # ruído leve
    Z += np.random.normal(0, 0.3, Z.shape)

    return X, Y, Z

# gerar
X, Y, Z = gerar_terreno_avancado(n=150)

# transformar em lista de pontos
df = pd.DataFrame({
    "X": X.flatten(),
    "Y": Y.flatten(),
    "Z": Z.flatten()
})

# salvar
df.to_csv("terreno_realista.csv", index=False)

print("Arquivo gerado!")