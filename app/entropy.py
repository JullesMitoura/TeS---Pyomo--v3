import pyomo.environ as pyo
import numpy as np
from app.aux.entropyAux import int_cp_T, enthalpy_T

class Entropy:
    def __init__(self, data, species, components, inhibited_component, equation='Ideal Gas'):
        self.data = data
        self.species = species
        self.components = components
        self.total_components = len(components)
        self.total_species = len(species)
        self.A = np.array([[component[specie] for specie in species] for component in data.values()])
        self.inhibited_component = inhibited_component
        self.equation = equation

    def identify_phases(self, phase_type):
        """
        Identifies the components that belong to the given phase type ('s' for solids, 'g' for gases).
        """
        return [i for i, comp in enumerate(self.data) if self.data[comp].get("Phase") == phase_type]

    def bnds_values(self, initial):
        """
        Returns the bounds for the variables based on the initial guess and the inhibited component.
        """
        max_species = np.dot(initial, self.A)
        epsilon = 1e-05
        bnds_aux = []

        if self.inhibited_component and self.inhibited_component != '---':
            try:
                aux_idx = next(index for index, value in self.data.items() if value['Component'] == self.inhibited_component)
            except StopIteration:
                print(f"Inhibited component '{self.inhibited_component}' not found.")
                aux_idx = None
        else:
            aux_idx = None

        for i, comp in enumerate(self.data):
            if aux_idx is not None and i == aux_idx:
                bnds_aux.append((1e-8, epsilon))
            else:
                a = np.multiply(1 / np.where(self.A[i] != 0, self.A[i], np.inf), max_species)
                upper_bound = np.min(a[a > 0]) if a[a > 0].size > 0 else epsilon
                bnds_aux.append((1e-8, max(upper_bound, epsilon)))

        return tuple(bnds_aux)
    
    def solve_entropy(self, initial, Tinit, P):
        bnds = self.bnds_values(initial)
        total_components = len(self.components)

        # Define o modelo Pyomo
        model = pyo.ConcreteModel()
        model.n = pyo.Var(range(total_components), domain=pyo.NonNegativeReals, bounds=lambda m, i: bnds[i])
        model.T = pyo.Var(domain=pyo.NonNegativeReals, initialize=Tinit)

        # Identifica componentes gasosos
        gases = self.identify_phases('g')

        # Define a função objetivo de entropia
        def entropy_rule(model):
            T0 = 298.15  # Temperatura de referência em K
            R = 8.314    # Constante universal dos gases em J/mol·K

            # Calcula entalpia integrada, delta H e delta G
            int_cp_T_values, deltaH, deltaG = int_cp_T(model.T, self.data)
            n_sum = sum(model.n[i] for i in range(total_components))

            # Calcula o potencial químico para gases
            entropy_i = [
                ((deltaH[i] - deltaG[i]) / T0) 
                - R * pyo.log(P) 
                - R * pyo.log((model.n[gases[i]] / (n_sum + 1e-8)))
                + int_cp_T_values[i]
                for i in range(len(gases))
            ]

            # Calcula a entropia total com um termo de regularização
            regularization_term = 1e-6
            entropy = sum(entropy_i[i] * model.n[gases[i]] for i in range(len(entropy_i))) + regularization_term
            return -entropy

        model.obj = pyo.Objective(rule=entropy_rule, sense=pyo.minimize)

        # Restrições de balanço de elementos
        model.element_balance = pyo.ConstraintList()
        for i in range(self.total_species):
            tolerance = 1e-6
            lhs = sum(self.A[j, i] * model.n[j] for j in range(total_components))
            rhs = sum(self.A[j, i] * initial[j] for j in range(total_components))
            model.element_balance.add(pyo.inequality(-tolerance, lhs - rhs, tolerance))

        enthalpy_exprs_final = enthalpy_T(model.T, self.data)
        enthalpy_exprs_initial= enthalpy_T(Tinit, self.data)
        initial_enthalpy_sum = sum(initial[j] * enthalpy_exprs_initial[j] for j in range(total_components))
        final_enthalpy_sum = sum(model.n[j] * enthalpy_exprs_final[j] for j in range(total_components))

        tolerance = 1e-6
        model.enthalpy_balance = pyo.Constraint(
            expr=pyo.inequality(-tolerance, final_enthalpy_sum - initial_enthalpy_sum, tolerance)
        )

        solver = pyo.SolverFactory('ipopt')
        results = solver.solve(model, tee=False)

        if results.solver.termination_condition == pyo.TerminationCondition.optimal:
            res = [pyo.value(model.n[i]) for i in range(total_components)]
            Teq = pyo.value(model.T)
            return res, Teq
        else:
            raise Exception("Optimal solution not found.")