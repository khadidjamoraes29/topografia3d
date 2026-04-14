import pandas as pd
import re

arquivo = "cordeiro.kml"

dados = []

with open(arquivo, "r", encoding="utf-8") as f:
    conteudo = f.read()

# separar cada placemark
placemarks = conteudo.split("<Placemark>")

for p in placemarks[1:]:

    # pegar altura do description
    desc_match = re.search(r"<description>(.*?)</description>", p)
    if desc_match:
        altura = float(desc_match.group(1).replace("m", "").strip())
    else:
        altura = 0

    # pegar coordenadas
    coords_match = re.search(r"<coordinates>(.*?)</coordinates>", p, re.DOTALL)
    if coords_match:
        coords_text = coords_match.group(1).strip()

        linhas = coords_text.split()

        for linha in linhas:
            partes = linha.split(",")

            if len(partes) >= 2:
                lon = float(partes[0])
                lat = float(partes[1])

                # usa Z do arquivo (mais confiável)
                if len(partes) >= 3:
                    z = float(partes[2])
                else:
                    z = altura

                dados.append([lon, lat, z])

# criar dataframe
df = pd.DataFrame(dados, columns=["X", "Y", "Z"])

# salvar
df.to_csv("curvas_nivel2.csv", index=False)

print("CSV gerado com sucesso!")