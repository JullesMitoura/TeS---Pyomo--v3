import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def linear_graph_maxs(dataframe, label1, label2, value1, value2, components, selected_components, name_colum, graph_type):
    filtered_data = dataframe[(dataframe[label1] == value1) & (dataframe[label2] == value2)]

    colors_list = [
        'lightseagreen', 'darkblue', 'salmon', 'tan', 'steelblue', 'dimgrey',
        'cornflowerblue', '#900C3F', '#581845', '#DAF7A6', '#FFC300',
        '#FF5733', '#8D6E63', '#1E88E5', '#43A047', '#7B1FA2', '#F57C00',
        '#0288D1', '#43A047', '#8BC34A', '#9C27B0', '#4CAF50', '#607D8B', '#FF7043'
    ]

    fig1, ax1 = plt.subplots(figsize=(8, 4))

    if graph_type == "N":
        x = filtered_data[name_colum]
        x_label = name_colum
    elif graph_type == "T":
        x = filtered_data['Initial Temperature']
        x_label = 'Initial Temperature'
    elif graph_type == "P":
        x = filtered_data['Pressure']
        x_label = 'Pressure'

    for idx, component in enumerate(components):
        if component in filtered_data.columns:
            y = filtered_data[component]
            ax1.plot(x, y, label=component, color=colors_list[idx % len(colors_list)])
    ax1.set_xlabel(x_label)
    ax1.set_ylabel('Mols')
    ax1.grid(True)
    ax1.legend(loc='upper left', bbox_to_anchor=(1.2, 1), fontsize='small')

    if 'Equilibrium Temperature (K)' in filtered_data.columns:
        ax1_twin = ax1.twinx()
        eq_temp = filtered_data['Equilibrium Temperature (K)']
        ax1_twin.plot(x, eq_temp, label='Equilibrium Temperature (K)', color='black', linestyle='--')
        ax1_twin.set_ylabel('Equilibrium Temperature (K)', color='black')
        ax1_twin.tick_params(axis='y', labelcolor='black')

    plt.tight_layout()
    plt.show()

    if len(selected_components) > 0:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        
        selected_data = filtered_data[selected_components]
        total_sum = selected_data.sum(axis=1)
        normalized_data = selected_data.div(total_sum, axis=0)

        for idx, component in enumerate(selected_components):
            if component in normalized_data.columns:
                y = normalized_data[component]
                ax2.plot(x, y, label=f"{component}", color=colors_list[idx % len(colors_list)])
        ax2.set_xlabel(x_label)
        ax2.set_ylabel('Molar Fraction')
        ax2.grid(True)
        ax2.legend(loc='upper left', bbox_to_anchor=(1.2, 1), fontsize='small')

        if 'Equilibrium Temperature (K)' in filtered_data.columns:
            ax2_twin = ax2.twinx()
            eq_temp = filtered_data['Equilibrium Temperature (K)']
            ax2_twin.plot(x, eq_temp, label='Equilibrium Temperature (K)', color='black', linestyle='--')
            ax2_twin.set_ylabel('Equilibrium Temperature (K)', color='black')
            ax2_twin.tick_params(axis='y', labelcolor='black')

        plt.tight_layout()
        plt.show()