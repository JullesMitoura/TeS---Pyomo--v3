import pandas as pd
from io import StringIO

# --- 1. Dados da aba "Informations"
informations_data = """Component,Phase,a,b,c,d,∆Hf298,∆Gf298,Pc,Tc,omega,Zc,Vc,Tmax,initial,C,H,O,N
Methane,g,1.702,0.009081,-0.000002164,0,-74520,-50460,45.99,190.6,0.012,0.286,98.6,1500,0,1,4,0,0
Water,g,3.47,0.00145,0,12100,-241818,-228572,220.55,647.1,0.345,0.229,55.9,1500,4.718,0,2,1,0
CarbonMonoxide,g,3.376,0.000557,0,-3100,-110525,-137169,34.99,132.9,0.048,0.299,93.4,1500,0,1,0,1,0
CarbonDioxide,g,5.457,0.001045,0,-115700,-393509,-394359,73.83,304.2,0.224,0.274,94.0,1500,0,1,0,2,0
Hydrogen,g,3.249,0.000422,0,8300,0,0,13.13,33.19,-0.216,0.305,64.1,1500,0,0,2,0,0
Carbon,s,1.771,0.000771,0,-86700,0,0,0,0,0,0,0,1500,0,1,0,0,0"""

df_info = pd.read_csv(StringIO(informations_data))
components = df_info["Component"].tolist()

# --- 2. Matriz kij completa (com muitos componentes)
full_kij_data = {
    "Methane": {"Methane": 0, "Water": 0.50, "Carbon Monoxide": 0.03, "Carbon Dioxide": 0.09, "Hydrogen": 0.03, "Carbon": 0},
    "Water": {"Methane": 0.50, "Water": 0, "Carbon Monoxide": 0.12, "Carbon Dioxide": 0.18, "Hydrogen": 0.35, "Carbon": 0},
    "Carbon Monoxide": {"Methane": 0.03, "Water": 0.12, "Carbon Monoxide": 0, "Carbon Dioxide": -0.01, "Hydrogen": -0.01, "Carbon": 0},
    "Carbon Dioxide": {"Methane": 0.09, "Water": 0.18, "Carbon Monoxide": -0.01, "Carbon Dioxide": 0, "Hydrogen": 0.10, "Carbon": 0},
    "Hydrogen": {"Methane": 0.03, "Water": 0.35, "Carbon Monoxide": -0.01, "Carbon Dioxide": 0.10, "Hydrogen": 0, "Carbon": 0},
    "Carbon": {"Methane": 0, "Water": 0, "Carbon Monoxide": 0, "Carbon Dioxide": 0, "Hydrogen": 0, "Carbon": 0}
}

# --- 3. Construir DataFrame kij com base apenas nos componentes da aba Informations
df_kij = pd.DataFrame(index=components, columns=components)

for row in components:
    for col in components:
        try:
            df_kij.loc[row, col] = full_kij_data.get(row, {}).get(col, 0)
        except KeyError:
            df_kij.loc[row, col] = 0

# --- 4. Salvar no Excel
with pd.ExcelWriter("thermodynamic_data_filtered.xlsx", engine="openpyxl") as writer:
    df_info.to_excel(writer, sheet_name="Informations", index=False)
    df_kij.to_excel(writer, sheet_name="kij")