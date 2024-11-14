import pyomo.environ as pyo

def int_cp_T(T, components):
    """
    Returns symbolic expressions for the integral of Cp/T for each component at a temperature T.

    Parameters:
    T (pyo.Var): Temperature in Kelvin, as a Pyomo variable.
    components (dict): Dictionary of components, each with their properties.

    Returns:
    tuple: List of symbolic integrals of Cp/T, list of ∆Hf298, and list of ∆Gf298 for each component.
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

        # Create symbolic expression for the integral of Cp/T from T0 to T
        integral_expr = R * (a * pyo.log(T / T0) + b * (T - T0) / 2 + c * (T ** 2 - T0 ** 2) / 3 + d * (1 / T - 1 / T0))

        results.append(integral_expr)
        DeltaH.append(deltaH)
        DeltaG.append(deltaG)

    return results, DeltaH, DeltaG