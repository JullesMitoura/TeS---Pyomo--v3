import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def linear_graph(dataframe, label1, label2, value1, value2, components, selected_components, name_colum, graph_type):
    filtered_data = dataframe[(dataframe[label1] == value1) & (dataframe[label2] == value2)]

    colors_list = [
    'lightseagreen',  # Red (Primary)
    'darkblue',  # Green (Primary)
    'salmon',  # Blue (Primary)
    'tan',  # Magenta
    'steelblue',  # Cyan
    'dimgrey',  # Orange
    'cornflowerblue',  # Crimson
    '#900C3F',  # Dark Red
    '#581845',  # Purple
    '#DAF7A6',  # Light Green
    '#FFC300',  # Gold
    '#FF5733',  # Coral
    '#8D6E63',  # Brown
    '#1E88E5',  # Light Blue
    '#43A047',  # Green (Darker)
    '#7B1FA2',  # Deep Purple
    '#F57C00',  # Amber
    '#0288D1',  # Blue (Darker)
    '#43A047',  # Teal
    '#8BC34A',  # Lime Green
    '#9C27B0',  # Violet
    '#4CAF50',  # Light Green
    '#607D8B',  # Blue Grey
    '#FF7043'   # Deep Orange
]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    if graph_type == "N":
        x = filtered_data[name_colum]
        for idx, component in enumerate(components):
            if component in filtered_data.columns:
                y = filtered_data[component]
                ax1.plot(x, y, label=component, color=colors_list[idx % len(colors_list)])  # Use color from the list
        ax1.set_xlabel(name_colum)
        ax1.set_ylabel('Mols')
        ax1.grid(True)

    elif graph_type == "T":
        x = filtered_data['Initial Temperature']
        for idx, component in enumerate(components):
            if component in filtered_data.columns:
                y = filtered_data[component]
                ax1.plot(x, y, label=component, color=colors_list[idx % len(colors_list)])  # Use color from the list
        ax1.set_xlabel('Initial Temperature')
        ax1.set_ylabel('Mols')
        ax1.grid(True)

    elif graph_type == "P":
        x = filtered_data['Pressure']
        for idx, component in enumerate(components):
            if component in filtered_data.columns:
                y = filtered_data[component]
                ax1.plot(x, y, label=component, color=colors_list[idx % len(colors_list)])  # Use color from the list
        ax1.set_xlabel('Pressure')
        ax1.set_ylabel('Mols')
        ax1.grid(True)
    
    ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize='small')

    if selected_components:
        if graph_type == "N":
            label = name_colum
            x = filtered_data[label]
        elif graph_type == "T":
            label = 'Initial Temperature'
            x = filtered_data[label]
        elif graph_type == "P":
            label = 'Pressure'
            x = filtered_data[label]

        selected_data = filtered_data[selected_components]
        total_sum = selected_data.sum(axis=1)
        normalized_data = selected_data.div(total_sum, axis=0)
        
        for idx, component in enumerate(selected_components):
            if component in normalized_data.columns:
                y = normalized_data[component]
                ax2.plot(x, y, label=f"{component}", color=colors_list[idx % len(colors_list)])  # Use color from the list
        
        ax2.set_xlabel(label)
        ax2.set_ylabel('Molar Fraction')
        ax2.grid(True)
        ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize='small')
    
    plt.tight_layout()
    plt.show()