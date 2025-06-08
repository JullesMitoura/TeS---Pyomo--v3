import numpy as np
import pandas as pd
import pyomo.environ as pyo
from app.find_path import resource_path

def load_kij(caminho_arquivo, 
             componentes):
    try:
        df_kij = pd.read_excel(caminho_arquivo, index_col=0)
        df_kij = df_kij.reindex(index=componentes, columns=componentes, fill_value=0)
        return df_kij
    except FileNotFoundError:
        return pd.DataFrame(0, index=componentes, columns=componentes)
    except Exception as e:
        print(f"Erro ao ler o arquivo kij: {e}. Todos os valores de kij serão considerados como 0.")
        return pd.DataFrame(0, index=componentes, columns=componentes)

def fug(T, 
                        P, 
                        eq, 
                        n, 
                        components,
                        kij_filepath=resource_path('kij.xlsx')):
    R = 8.314462    # J/(mol*K)
    P_pa = P * 1e5  # Converte pressão de bar para Pa

    comp_names = list(components.keys())
    total_n = sum(n)
    if total_n == 0:
        return [np.nan] * len(comp_names)
    
    if not comp_names:
        return []

    mole_fractions = {name: n_i / total_n for name, n_i in zip(comp_names, n)}
    resultados_lista = [0.0] * len(comp_names)

    gas_components = {name: data for name, data in components.items() if data['Phase'].lower() != 's'}
    solid_components = {name: data for name, data in components.items() if data['Phase'].lower() == 's'}
    
    for name in solid_components:
        idx = comp_names.index(name)
        resultados_lista[idx] = 1.0
        
    if not gas_components:
        return resultados_lista

    if eq == 'Ideal Gas':
        for name in gas_components:
            idx = comp_names.index(name)
            resultados_lista[idx] = 1.0
        return resultados_lista

    gas_comp_names = list(gas_components.keys())
    y = np.array([mole_fractions[name] for name in gas_comp_names])
    
    df_kij = load_kij(kij_filepath, gas_comp_names)

    eos_params = {
        'Peng-Robinson': {
            'Omega_a': 0.45724, 'Omega_b': 0.07780,
            'm_func': lambda w: 0.37464 + 1.54226 * w - 0.26992 * w**2,
            'alpha_func': lambda Tr_scalar, m_scalar: (1 + m_scalar * (1 - pyo.sqrt(Tr_scalar)))**2,
            'Z_coeffs': lambda A, B: [1, B - 1, A - 2*B - 3*B**2, -A*B + B**2 + B**3],
            'ln_phi_term': lambda Z, B: (1 / (2 * np.sqrt(2))) * np.log((Z + (1 + np.sqrt(2)) * B) / (Z + (1 - np.sqrt(2)) * B))
        },
        'Soave-Redlich-Kwong': {
            'Omega_a': 0.42748, 'Omega_b': 0.08664,
            'm_func': lambda w: 0.480 + 1.574 * w - 0.176 * w**2,
            'alpha_func': lambda Tr_scalar, m_scalar: (1 + m_scalar * (1 - pyo.sqrt(Tr_scalar)))**2,
            'Z_coeffs': lambda A, B: [1, -1, A - B - B**2, -A*B],
            'ln_phi_term': lambda Z, B: np.log(1 + B/Z)
        },
        'Redlich-Kwong': {
            'Omega_a': 0.42748, 'Omega_b': 0.08664,
            'm_func': lambda w: 0,
            'alpha_func': lambda Tr_scalar, m_scalar: 1 / pyo.sqrt(Tr_scalar),
            'Z_coeffs': lambda A, B: [1, -1, A - B - B**2, -A*B],
            'ln_phi_term': lambda Z, B: np.log(1 + B/Z)
        }
    }
    
    if eq not in eos_params:
        raise ValueError(f"Equação de estado '{eq}' não suportada.")
    
    params = eos_params[eq]
    
    Tc = np.array([gas_components[name]['Tc'] for name in gas_comp_names])
    Pc = np.array([gas_components[name]['Pc'] * 1e5 for name in gas_comp_names])
    omega = np.array([gas_components[name]['omega'] for name in gas_comp_names])

    m = params['m_func'](omega)
    Tr = T / Tc
    
    alpha = np.zeros_like(Tr)
    for i in range(len(gas_comp_names)):
        alpha[i] = params['alpha_func'](Tr[i], m[i])
    
    a_i = params['Omega_a'] * (R**2 * Tc**2 / Pc) * alpha
    b_i = params['Omega_b'] * (R * Tc / Pc)
    
    a_ij = (1 - df_kij.values) * np.sqrt(np.outer(a_i, a_i))
    
    a_mix = np.sum(np.outer(y, y) * a_ij)
    b_mix = np.sum(y * b_i)
    
    A = a_mix * P_pa / (R**2 * T**2)
    B = b_mix * P_pa / (R * T)
    
    coeffs = params['Z_coeffs'](A, B)
    Z_roots = np.roots(coeffs)
    
    real_roots = Z_roots[np.isreal(Z_roots)].real
    positive_real_roots = real_roots[real_roots > 0]
    if len(positive_real_roots) == 0:
        for name in gas_components:
            idx = comp_names.index(name)
            resultados_lista[idx] = np.nan
        return resultados_lista

    Z = positive_real_roots.max()
    if Z <= B:
        for name in gas_components:
            idx = comp_names.index(name)
            resultados_lista[idx] = np.nan
        return resultados_lista

    term1 = b_i / b_mix * (Z - 1)
    term2 = -np.log(Z - B)
    
    sum_y_a_ij = np.dot(y, a_ij)
    
    term3_dyn = (2 * sum_y_a_ij / a_mix) - (b_i / b_mix)
    term3_log = params['ln_phi_term'](Z, B)
    
    ln_phi_i = term1 + term2 - (A / B) * term3_dyn * term3_log
    
    phi_i = np.exp(ln_phi_i)

    for i, name in enumerate(gas_comp_names):
        idx = comp_names.index(name)
        resultados_lista[idx] = phi_i[i] 
    return resultados_lista