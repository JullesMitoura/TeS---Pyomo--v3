import numpy as np
import pandas as pd
import pyomo.environ as pyo

def fug(T,                          # Temperature K
        P,                          # Pressure bar
        eq,                         # Name of equation to calculate phi(L,V)
        n,                          # Molar fraction of components
        components,                 # Thermodynamic data about components
        kij_df: pd.DataFrame):      # Dataframe with kij parameters
    
    R = 8.314462    # Constante universal dos gases em J/(mol*K) ou Pa*m^3/(mol*K)
    P_pa = P * 1e5  # Converte pressão de bar para Pa

    comp_names = list(components.keys())
    total_n = sum(n)
    
    if total_n == 0:
        return [np.nan] * len(comp_names)
    
    if not comp_names:
        return []

    mole_fractions = {name: n_i / total_n for name, n_i in zip(comp_names, n)}
    resultados_lista = [0.0] * len(comp_names)

    gas_components = {name: data for name, data in components.items() if data.get('Phase', 'g').lower() != 's'}
    solid_components = {name: data for name, data in components.items() if data.get('Phase', 'g').lower() == 's'}
    
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
    
    df_kij = kij_df.reindex(index=gas_comp_names, columns=gas_comp_names, fill_value=0)

    if np.any(df_kij.values != 0):
        print(f"INFO (fug): Parâmetros de interação binária (kij) não-nulos foram encontrados e serão considerados nos cálculos da EoS '{eq}'.")
    else:
        print(f"INFO (fug): A matriz Kij consiste apenas em zeros. Os cálculos da EoS '{eq}' prosseguirão assumindo interações ideais (kij = 0).")

    # Equação Virial (Truncada no 2º Coeficiente)
    if eq == 'Virial':
        Tc = np.array([gas_components[name]['Tc'] for name in gas_comp_names])
        omega = np.array([gas_components[name]['omega'] for name in gas_comp_names])
        Zc = np.array([gas_components[name]['Zc'] for name in gas_comp_names])
        Vc_cm3_mol = np.array([gas_components[name]['Vc'] for name in gas_comp_names])
        
        # Converte Vc para m^3/mol
        Vc = Vc_cm3_mol / 1e6

        kij = df_kij.values
        num_comps = len(gas_comp_names)
        B_matrix = np.zeros((num_comps, num_comps))

        for i in range(num_comps):
            for j in range(num_comps):
                Tcij = np.sqrt(Tc[i] * Tc[j]) * (1 - kij[i, j])
                wij = (omega[i] + omega[j]) / 2
                Vcij = ((Vc[i]**(1/3) + Vc[j]**(1/3)) / 2)**3
                Zcij = (Zc[i] + Zc[j]) / 2
                Pcij_pa = Zcij * R * Tcij / Vcij
                
                Tr_ij = T / Tcij
                B0 = 0.083 - 0.422 / (Tr_ij**1.6)
                B1 = 0.139 - 0.172 / (Tr_ij**4.2)
                B_matrix[i, j] = (R * Tcij / Pcij_pa) * (B0 + wij * B1)
        
        B_mix = y.T @ B_matrix @ y
        sum_yB = B_matrix @ y
        ln_phi_k = (2 * sum_yB - B_mix) * P_pa / (R * T)
        
        phi_k = np.exp(ln_phi_k)

        for i, name in enumerate(gas_comp_names):
            idx = comp_names.index(name)
            resultados_lista[idx] = phi_k[i]
            
        return resultados_lista

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
            'm_func': lambda w: np.zeros_like(w), 
            'alpha_func': lambda Tr_scalar, m_scalar: 1 / pyo.sqrt(Tr_scalar),
            'Z_coeffs': lambda A, B: [1, -1, A - B - B**2, -A*B],
            'ln_phi_term': lambda Z, B: np.log(1 + B/Z)
        }
    }
    
    if eq not in eos_params:
        raise ValueError(f"Equação de estado '{eq}' não suportada.")
    
    params = eos_params[eq]
    
    Tc = np.array([gas_components[name]['Tc'] for name in gas_comp_names])
    Pc = np.array([gas_components[name]['Pc'] * 1e5 for name in gas_comp_names]) # Usa Pa
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