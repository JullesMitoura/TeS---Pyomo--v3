import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

def calculate_vle(model, 
                  experimental_data, 
                  kij, 
                  mode='isothermal'):
    if mode not in ['isothermal', 'isobaric']:
        raise ValueError("O modo deve ser 'isothermal' ou 'isobaric'")

    x1_exp = experimental_data['x1'].values
    y1_exp = experimental_data['y1'].values
    results_calc = []

    if mode == 'isothermal':
        T = experimental_data['T'].iloc[0]
        P_exp = experimental_data['P'].values

        for idx, x1 in enumerate(x1_exp):
            x = np.array([x1, 1-x1])
            P_guess = P_exp[idx]
            y1_guess = y1_exp[idx] if pd.notna(y1_exp[idx]) else x1

            def objective(vars):
                P, y1 = vars
                y = np.array([y1, 1-y1])
                am_L, bm_L = model._get_mixture_params(T, x, kij)
                Zl, _ = model._solve_eos_for_Z(am_L, bm_L, P, T)
                phi_L = model._get_fugacity_coeffs(Zl, am_L, bm_L, P, T, x, kij)
                am_V, bm_V = model._get_mixture_params(T, y, kij)
                _, Zv = model._solve_eos_for_Z(am_V, bm_V, P, T)
                phi_V = model._get_fugacity_coeffs(Zv, am_V, bm_V, P, T, y, kij)
                return [x[0]*phi_L[0] - y[0]*phi_V[0], x[1]*phi_L[1] - y[1]*phi_V[1]]
            
            sol = least_squares(objective, [P_guess, y1_guess], bounds=([0, 0], [np.inf, 1]))
            if sol.success:
                results_calc.append({'P_calc': sol.x[0], 'y1_calc': sol.x[1]})
            else:
                results_calc.append({'P_calc': np.nan, 'y1_calc': np.nan})

    else:  # 'isobaric'
        P = experimental_data['P'].iloc[0]
        T_exp = experimental_data['T'].values
        
        for idx, x1 in enumerate(x1_exp):
            x = np.array([x1, 1-x1])
            T_guess = T_exp[idx]
            y1_guess = y1_exp[idx] if pd.notna(y1_exp[idx]) else x1

            def objective(vars):
                T, y1 = vars
                y = np.array([y1, 1-y1])
                am_L, bm_L = model._get_mixture_params(T, x, kij)
                Zl, _ = model._solve_eos_for_Z(am_L, bm_L, P, T)
                phi_L = model._get_fugacity_coeffs(Zl, am_L, bm_L, P, T, x, kij)
                am_V, bm_V = model._get_mixture_params(T, y, kij)
                _, Zv = model._solve_eos_for_Z(am_V, bm_V, P, T)
                phi_V = model._get_fugacity_coeffs(Zv, am_V, bm_V, P, T, y, kij)
                return [x[0]*phi_L[0] - y[0]*phi_V[0], x[1]*phi_L[1] - y[1]*phi_V[1]]

            sol = least_squares(objective, [T_guess, y1_guess], bounds=([0, 0], [np.inf, 1]))
            if sol.success:
                results_calc.append({'T_calc': sol.x[0], 'y1_calc': sol.x[1]})
            else:
                results_calc.append({'T_calc': np.nan, 'y1_calc': np.nan})

    return pd.DataFrame(results_calc)


def create_vle_plot(components, experimental_data, calculated_data, kij, eos_name, mode):
    """
    Cria a figura do matplotlib com os gráficos de comparação, mas não a exibe.
    
    Retorna:
        matplotlib.figure.Figure: O objeto da figura para ser usado externamente.
    """
    background_color = "#F8F9FA"
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.5), facecolor=background_color)

    x1_exp = experimental_data['x1']
    y1_exp = experimental_data['y1']
    y1_calc = calculated_data['y1_calc']

    if mode == 'isothermal':
        T = experimental_data['T'].iloc[0]
        P_exp = experimental_data['P']
        P_calc = calculated_data['P_calc']
        
        valid = pd.notna(P_calc)
        if valid.sum() > 1:
            sort_idx = np.argsort(x1_exp[valid])
            ax1.plot(x1_exp[valid].iloc[sort_idx], P_calc[valid].iloc[sort_idx], 'b-', label='Calculado (x1)')
            ax1.plot(y1_calc[valid].iloc[sort_idx], P_calc[valid].iloc[sort_idx], 'r-', label='Calculado (y1)')

        ax1.plot(x1_exp, P_exp, 'bo', label='Experimental (x1)')
        ax1.plot(y1_exp, P_exp, 'ro', label='Experimental (y1)')
        ax1.set_xlabel('Fração molar de ' + components[0])
        ax1.set_ylabel('Pressão (bar)')
        ax1.set_title(f'Diagrama Pxy a {T:.2f} K\nEOS: {eos_name}, kij={kij:.4f}')

    else:  # 'isobaric'
        P = experimental_data['P'].iloc[0]
        T_exp = experimental_data['T']
        T_calc = calculated_data['T_calc']

        valid = pd.notna(T_calc)
        if valid.sum() > 1:
            sort_idx = np.argsort(x1_exp[valid])
            ax1.plot(x1_exp[valid].iloc[sort_idx], T_calc[valid].iloc[sort_idx], 'b-', label='Calculado (x1)')
            ax1.plot(y1_calc[valid].iloc[sort_idx], T_calc[valid].iloc[sort_idx], 'g-', label='Calculado (y1)')

        ax1.plot(x1_exp, T_exp, 'bo', label='Experimental (x1)')
        ax1.plot(y1_exp, T_exp, 'ro', label='Experimental (y1)')
        ax1.set_xlabel('Fração molar de ' + components[0])
        ax1.set_ylabel('Temperatura (K)')
        ax1.set_title(f'Diagrama Txy a {P:.2f} bar\nEOS: {eos_name}, kij={kij:.4f}')

    ax1.legend()
    ax1.grid(True)
    valid_xy = pd.notna(y1_calc)
    if valid_xy.sum() > 1:
        sort_idx = np.argsort(x1_exp[valid_xy])
        ax2.plot(x1_exp[valid_xy].iloc[sort_idx], y1_calc[valid_xy].iloc[sort_idx], 'r-', label='Calculado')

    ax2.plot(x1_exp, y1_exp, 'ro', label='Experimental')
    ax2.plot([0, 1], [0, 1], 'k--')
    ax2.set_xlabel('Fração molar líquida (x) de ' + components[0])
    ax2.set_ylabel('Fração molar vapor (y) de ' + components[0])
    ax2.set_title('Diagrama de Equilíbrio y-x')
    
    ax2.legend()
    ax2.grid(True)
    ax2.set_aspect('equal', 'box')

    fig.tight_layout(pad=0.8)
    return fig