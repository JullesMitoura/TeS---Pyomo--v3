import pyomo.environ as pyo

def int_cp_T(T, components):
    """
    Returns numerical expressions for the integral of Cp/T from T0 to T for each component.
    """
    R = 8.314  # Gas constant in J/(mol·K)
    T0 = 298.15  # Reference temperature in Kelvin
    
    results = []
    DeltaH = []
    DeltaG = []

    for component in components.values():
        deltaH = component.get('∆Hf298', 0)
        deltaG = component.get('∆Gf298', 0)

        a = component.get('a', 0)
        b = component.get('b', 0)
        c = component.get('c', 0)
        d = component.get('d', 0)

        term1 = a * pyo.log(T / T0)
        term2 = b * (T - T0)
        term3 = (c / 2) * (T**2 - T0**2)
        term4 = (-d / 2) * (1 / T**2 - 1 / T0**2)

        integral_value = R * (term1 + term2 + term3 + term4)
        
        # Append the results
        results.append(integral_value)
        DeltaH.append(deltaH)
        DeltaG.append(deltaG)

    return results, DeltaH, DeltaG

def enthalpy_T(T, components):
    """
    Returns symbolic expressions for the enthalpy at a temperature T for each component.
    """
    R = 8.314  # Gas constant in J/(mol·K)
    T0 = 298.15  # Reference temperature in Kelvin
    
    results = []

    for component in components.values():
        deltaH = component.get('∆Hf298', 0)
        a = component.get('a', 0)
        b = component.get('b', 0)
        c = component.get('c', 0)
        d = component.get('d', 0)

        term1 = a * (T - T0)
        term2 = (b / 2) * (T**2 - T0**2)
        term3 = (c / 3) * (T**3 - T0**3)
        term4 = -d * (1 / T - 1 / T0)

        integral_value = R * (term1 + term2 + term3 + term4)
        
        # Total enthalpy expression at temperature T
        enthalpy_expr = deltaH + integral_value
        results.append(enthalpy_expr)
        
    return results