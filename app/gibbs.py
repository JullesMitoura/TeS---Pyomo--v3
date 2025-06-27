import pyomo.environ as pyo
import numpy as np
from app.auxiliar_func.gibbsZero import gibbs_pad
from app.auxiliar_func.eos import fug
from app.auxiliar_func.get_solver import get_ipopt_solver

class Gibbs:
    def __init__(self, data, species, components, inhibited_component,kij, equation='Ideal Gas'):
        self.data = data
        self.species = species
        self.components = components
        self.total_components = len(components)
        self.total_species = len(species)
        self.A = np.array([[component[specie] for specie in species] for component in data.values()])
        self.inhibited_component = inhibited_component
        self.equation = equation
        self.kij = kij


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

    def solve_gibbs(self, initial, T, P, progress_callback=None):
        initial[initial == 0] = 0.00001
        bnds = self.bnds_values(initial)
        model = pyo.ConcreteModel()
        model.n = pyo.Var(range(self.total_components), domain=pyo.NonNegativeReals, bounds=lambda m, i: bnds[i])

        solids = self.identify_phases('s')
        gases = self.identify_phases('g')

        def gibbs_rule(model):
            R = 8.314  # J/mol·K
            df_pad = gibbs_pad(T, self.data)
            phii = fug(T=T, P=P, eq=self.equation, n=model.n, components=self.data, kij_df=self.kij)

            if isinstance(phii, (int, float)):  
                phii = [phii] * self.total_components

            mi_gas = [
                df_pad[i] + R * T * (
                    pyo.log(phii[i]) + 
                    pyo.log(model.n[i] / sum(model.n[j] for j in range(self.total_components))) + 
                    pyo.log(P)
                ) for i in gases
            ]

            mi_solids = [df_pad[i] for i in solids]

            regularization_term = 1e-6
            total_gibbs = sum(mi_gas[i] * model.n[gases[i]] for i in range(len(mi_gas))) + \
                        sum(mi_solids[i] * model.n[solids[i]] for i in range(len(mi_solids))) + \
                        regularization_term
            
            return total_gibbs

        model.obj = pyo.Objective(rule=gibbs_rule, sense=pyo.minimize)
        model.element_balance = pyo.ConstraintList()
        for i in range(self.total_species):
            tolerance = 1e-8
            lhs = sum(self.A[j, i] * model.n[j] for j in range(self.total_components))
            rhs = sum(self.A[j, i] * initial[j] for j in range(self.total_components))
            model.element_balance.add(pyo.inequality(-tolerance, lhs - rhs, tolerance))

        # Solver
        solver = get_ipopt_solver()

        solver.options['tol'] = 1e-8
        solver.options['max_iter'] = 5000
        results = solver.solve(model, tee=False)

        if results.solver.termination_condition == pyo.TerminationCondition.optimal:
            return [pyo.value(model.n[i]) for i in range(self.total_components)]
        else:
            raise Exception("Optimal solution not found.")