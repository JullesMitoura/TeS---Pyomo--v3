import pandas as pd
import numpy as np
from app.entropy import Entropy

class RunEntropy():
    def __init__(self, data, species, initial, components, Tmin, Tmax, Pmin, Pmax, nT, nP, 
                 reference_componente=None, reference_componente_min=None, reference_componente_max=None, n_reference_componente=None, inhibit_component=None,
                 state_equation='Ideal Gas'):
        self.data = data
        self.species = species
        self.initial = np.array(initial)
        self.components = components
        self.inhibit_component = inhibit_component
        self.Tmin = Tmin
        self.Tmax = Tmax
        self.Pmin = Pmin
        self.Pmax = Pmax
        self.nT = nT
        self.nP = nP
        self.reference_componente = reference_componente
        self.reference_componente_min = reference_componente_min
        self.reference_componente_max = reference_componente_max
        self.n_reference_componente = n_reference_componente
        self.state_equation = state_equation

    def format_data(self):
        if self.reference_componente is not None and self.reference_componente != '---':
            try:
                reference_index = np.where(self.components == self.reference_componente)[0][0]
            except IndexError:
                print(f"Erro: Componente de referência '{self.reference_componente}' não encontrado na lista de componentes.")
                reference_index = None
                n = None
            else:
                n = np.linspace(self.reference_componente_min, self.reference_componente_max, self.n_reference_componente)
        else:
            n = None
            reference_index = None

        T = np.linspace(self.Tmin, self.Tmax, self.nT)
        P = np.linspace(self.Pmin, self.Pmax, self.nP)

        return T, P, n, reference_index
    
    def run_entropy(self):
        gibbs = Entropy(self.data, self.species, self.components, self.inhibit_component, self.state_equation)
        T_vals, P_vals, n_vals, reference_index = self.format_data()
        results = pd.DataFrame(columns=self.components)

        result_list = []

        for T in T_vals:
            for P in P_vals:
                if reference_index is not None:
                    for n in n_vals:
                        initial_copy = self.initial.astype(float).copy()
                        initial_copy[reference_index] = n
                        result, Teq = gibbs.solve_entropy(initial_copy, T, P)

                        result_dict = {comp: round(val, 3) for comp, val in zip(self.components, result)}
                        result_dict[self.components[reference_index] + ' Initial'] = n
                        result_dict['Equilibrium Temperature (K)'] = Teq
                        result_dict.update({'Initial Temperature': T, 'Pressure': P})
                        result_list.append(result_dict)
                else:
                    result, Teq = gibbs.solve_entropy(self.initial, T, P)
                    result_dict = {comp: round(val, 3) for comp, val in zip(self.components, result)}
                    result_dict.update({'Initial Temperature': T, 'Pressure': P})
                    
                    result_list.append(result_dict)

        results = pd.concat([pd.DataFrame([result]) for result in result_list], ignore_index=True)

        return results.round(3)