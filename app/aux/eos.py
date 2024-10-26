import numpy as np
import pyomo.environ as pyo

def fug(T, P, eq, n, components):
    P = P * 100000  # bar -> Pa
    total_n = sum(n)
    mole_fractions = [ni / total_n for ni in n]
    
    if all(components[i]['C'] == 1 for i in components):
        return 1 
    if eq == 'Ideal Gas':
        return 1 
    
    Tc_aux = [components[i]['Tc'] for i in components]
    Pc_aux = [components[i]['Pc'] * 100000 for i in components]  # bar -> Pa
    omega_aux = [components[i]['omega'] for i in components]

    Tc = sum(mole_fractions[i] * Tc_aux[i] for i in range(len(components)))
    Pc = sum(mole_fractions[i] * Pc_aux[i] for i in range(len(components)))
    omega = sum(mole_fractions[i] * omega_aux[i] for i in range(len(components)))

    R = 8.314  # J/(mol*K)
    Tr = T / Tc
    Pr = P / Pc

    eos_params = {
        'Peng-Robinson': {'a': 0.45724, 'b': 0.07780, 'c': 2, 'd': 2},
        'Redlich Kwong': {'a': 0.42748, 'b': 0.08664, 'c': 2.0, 'd': 2.5},
        'Soave Redlich Kwong': {'a': 0.42748, 'b': 0.08664, 'c': 2.0, 'd': 2.5}
    }
    
    if eq not in eos_params:
        raise ValueError(f"Equação de estado {eq} não suportada.")
    
    params = eos_params[eq]

    a = params['a'] * (R**params['c'] * Tc**params['d']) / Pc
    b = params['b'] * (R * Tc) / Pc
    
    def calc_alpha_and_Z_vapor(Tr, Pr, eq, omega, a, b, R, T, P):
        if eq == 'Peng-Robinson':
            kappa = 0.37464 + 1.54226 * omega - 0.26992 * omega**2
            alpha = (1 + kappa * (1 - pyo.sqrt(Tr)))**2
        elif eq == 'Redlich Kwong':
            alpha = (1 + 0.401 * omega)
        elif eq == 'Soave Redlich Kwong':
            m = 0.48 + 1.574 * omega - 0.176 * omega**2
            alpha = (1 + m * (1 - pyo.sqrt(Tr)))**2  
        else:
            raise ValueError(f"Equação de estado {eq} não suportada.")
        
        a_alpha = a * alpha
        b_alpha = b
        
        A = a_alpha * P / (R**params['c'] * T**params['d'])
        B = b_alpha * P / (R * T)
        
        coefficients = [1, -1, A - B - B**2, -A * B]
        Z_roots = np.roots(coefficients)
        Z_vapor = Z_roots[np.isreal(Z_roots) & (Z_roots > 0)].real[0]
        
        return alpha, Z_vapor, b_alpha, B, A
    
    alpha, Z_vapor, b_alpha, B, A = calc_alpha_and_Z_vapor(Tr, Pr, eq, omega, a, b, R, T, P)
    ln_phi = (b_alpha / b) * (Z_vapor - 1) - np.log(Z_vapor - B) + A / (2 * np.sqrt(2) * B) * np.log((Z_vapor + (1 + np.sqrt(2)) * B) / (Z_vapor + (1 - np.sqrt(2)) * B))
    
    phi = np.exp(ln_phi)
    
    return phi