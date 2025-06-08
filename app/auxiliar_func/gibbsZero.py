import numpy as np
from scipy.integrate import quad

def gibbs_pad(T, components):
    """
    Calculates the chemical potential (mu_i) for the given components at a temperature T.

    Parameters:
    T (float): Temperature in Kelvin.
    components (dict): Dictionary of components, each with its properties.

    Returns:
    list: List of chemical potentials calculated for each component.
    """
    R = 8.314  # Gas constant in J/(mol·K)
    T0 = 298.15  # Reference temperature in Kelvin
    
    results = []

    for component in components.values():
        deltaH = component.get('∆Hf298', 0)
        deltaG = component.get('∆Gf298', 0)
        a = component.get('a', 0)
        b = component.get('b', 0)
        c = component.get('c', 0)
        d = component.get('d', 0)

        def cp(T_prime):
            return R * (a + b * T_prime + c * T_prime ** 2 + d / T_prime ** 2)

        def inner_integral(T_prime):
            value, _ = quad(cp, T0, T_prime)
            return (deltaH + value) / T_prime ** 2

        integral_value, _ = quad(inner_integral, T0, T)
        mu_i = T * (deltaG / T0 - integral_value)
        results.append(mu_i)

    return results