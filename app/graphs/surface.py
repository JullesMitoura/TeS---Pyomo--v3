import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_superficie(data, x, y, z):
    x_values = data[x].values
    y_values = data[y].values
    z_values = data[z].values
    
    # Obter valores únicos
    unique_x = np.unique(x_values)
    unique_y = np.unique(y_values)
    
    # Criar uma grade de contorno
    x_grid, y_grid = np.meshgrid(unique_x, unique_y)

    # Redimensionar z_values para a grade
    z_grid = np.zeros_like(x_grid)

    # Preencher a grade com os valores de z
    for i in range(len(unique_x)):
        for j in range(len(unique_y)):
            # Filtrar os dados para o ponto específico
            mask = (x_values == unique_x[i]) & (y_values == unique_y[j])
            if np.any(mask):
                z_grid[j, i] = z_values[mask][0]  # Supondo que há pelo menos um valor para cada combinação

    fig = plt.figure(figsize=(10, 4))

    ax1 = fig.add_subplot(121, projection='3d')
    surf = ax1.plot_surface(x_grid, y_grid, z_grid, cmap='coolwarm', edgecolor='none')
    ax1.set_xlabel(x, labelpad=10, fontsize=9, style='italic')
    ax1.set_ylabel(y, labelpad=10, fontsize=9, style='italic')
    cbar1 = fig.colorbar(surf, ax=ax1, pad=0.1)
    cbar1.ax.set_title(label=f'{z} (mols)', pad=5, fontweight='bold')

    ax2 = fig.add_subplot(122)
    c = ax2.contourf(x_grid, y_grid, z_grid, cmap='coolwarm', levels=50)
    ax2.set_xlabel(x, labelpad=10, fontsize=9, style='italic')
    ax2.set_ylabel(y, labelpad=10, fontsize=9, style='italic')
    cbar2 = plt.colorbar(c, ax=ax2, pad=0.1)
    cbar2.ax.set_title(label=f'{z} (mols)', pad=10, fontweight='bold')

    plt.tight_layout()
    plt.show()