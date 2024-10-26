import pyomo.environ as pyo
import numpy as np
from app.aux.gibbsZero import gibbs_pad
from app.aux.eos import fug

class Gibbs:
    def __init__(self, data, species, components, inhibited_component, equation = 'Ideal Gas'):
        self.data = data
        self.species = species
        self.components = components
        self.total_components = len(self.components)
        self.total_species = len(self.species)
        self.A = np.array([[component[specie] for specie in species] for component in data.values()])
        self.inhibited_component = inhibited_component
        self.equation = equation
        
    def bnds_values(self, initial):
        max_species = np.dot(initial, self.A)  # Produto escalar para obter max_species
        epsilon = 1e-05
        bnds_aux = []

        # Obter o índice do componente inibido (se existir)
        if self.inhibited_component != '---' and self.inhibited_component is not None:
            try:
                aux_idx = next(index for index, value in self.data.items() if value['Component'] == self.inhibited_component)
            except StopIteration:
                print(f"Componente inibido '{self.inhibited_component}' não encontrado.")
                aux_idx = None
        else:
            aux_idx = None

        # Iterar sobre os componentes e calcular os bounds
        for i, comp in enumerate(self.data):
            if aux_idx is not None and i == aux_idx:
                # Para o componente inibido, definir limites muito pequenos
                bnds_aux.append((1e-8, epsilon))
            else:
                # Calcular upper_bound para os demais componentes
                a = np.multiply(1 / np.where(self.A[i] != 0, self.A[i], np.inf), max_species)
                upper_bound = np.min(a[a > 0]) if a[a > 0].size > 0 else epsilon
                bnds_aux.append((1e-8, max(upper_bound, epsilon)))

        return tuple(bnds_aux)

    def solve_gibbs(self, initial, T, P):
        initial[initial == 0] = 0.0001
        bnds = self.bnds_values(initial)
        print(bnds)
        model = pyo.ConcreteModel()
        model.n = pyo.Var(range(self.total_components), domain=pyo.NonNegativeReals, bounds=lambda m, i: bnds[i])
        def gibbs_rule(model):
            R = 8.314  # J/mol·K
            dfg_gas = gibbs_pad(T, self.data)
            phii = fug(T = T, P = P, eq = self.equation, n = model.n, components= self.data)
            mi_gas = [
                dfg_gas[i] + R * T * (
                    pyo.log(phii) + 
                    pyo.log(model.n[i] / sum(model.n[j] for j in range(self.total_components))) + 
                    pyo.log(P)
                ) for i in range(self.total_components)
            ]

            regularization_term = 1e-4
            total_gibbs = sum(mi_gas[i] * model.n[i] for i in range(self.total_components)) + regularization_term
            return total_gibbs

        model.obj = pyo.Objective(rule=gibbs_rule, sense=pyo.minimize)

        def element_balance_rule(model, i):
            tolerance = 1e-8
            left_hand_side = sum(self.A[j, i] * model.n[j] for j in range(self.total_components))
            right_hand_side = sum(self.A[j, i] * initial[j] for j in range(self.total_components))
            return pyo.inequality(-tolerance, left_hand_side - right_hand_side, tolerance)

        for i in range(self.total_species):
            def create_constraint(i):
                return pyo.Constraint(rule=lambda m: element_balance_rule(m, i))
        
            setattr(model, f'element_balance_{i + 1}', create_constraint(i))

        solver = pyo.SolverFactory('ipopt')
        solver.options['tol'] = 1e-8
        results = solver.solve(model, tee=False)

        if results.solver.termination_condition == pyo.TerminationCondition.optimal:
            return [pyo.value(model.n[i]) for i in range(self.total_components)]
        else:
            raise Exception("Optimal solution not found.")