import pandas as pd
import numpy as np
import pyomo.environ as pyo
from app.auxiliar_func.get_solver import get_ipopt_solver

class VLE_Model:
    def __init__(self, 
                 components, 
                 component_props, 
                 eos_name: str = 'Peng-Robinson'):
        self.R = 83.1446  # cm³.bar/(mol.K)
        self.components = components
        self.props = component_props
        self.eos_name = eos_name.lower()

        # Set EOS-specific parameters
        if self.eos_name == 'peng-robinson':
            self.m_kappa = lambda w: 0.37464 + 1.54226 * w - 0.26992 * w**2
            self.Omega_a = 0.45724
            self.Omega_b = 0.07780
            self.delta1 = 1 + np.sqrt(2)
            self.delta2 = 1 - np.sqrt(2)
        elif self.eos_name == 'soave-redlich-kwong':
            self.m_kappa = lambda w: 0.480 + 1.574 * w - 0.176 * w**2
            self.Omega_a = 0.42748
            self.Omega_b = 0.08664
            self.delta1 = 1
            self.delta2 = 0
        elif self.eos_name == 'redlich-kwong':
            self.m_kappa = lambda w: 0.0  # RK não usa kappa
            self.Omega_a = 0.42748
            self.Omega_b = 0.08664
            self.delta1 = None
            self.delta2 = None
        else:
            raise ValueError("Equação de estado não suportada. Use 'Peng-Robinson', 'Soave-Redlich-Kwong' ou 'Redlich-Kwong'.")

        self.a_pure_params, self.b_pure_params = self._calculate_pure_params()

    def _calculate_pure_params(self):
        """Calculate pure component parameters a and b for each component."""
        a_params = {}
        b_params = {}
        for comp in self.components:
            Tc, Pc, omega = self.props[comp]
            a_params[comp] = self.Omega_a * (self.R**2 * Tc**2 / Pc)
            b_params[comp] = self.Omega_b * self.R * Tc / Pc
        return a_params, b_params

    def _get_alpha(self, T, comp):
        if self.eos_name == 'redlich-kwong':
            return (self.props[comp][0] / T)**0.5  # sqrt(Tc / T)
        else:
            Tc, _, omega = self.props[comp]
            kappa = self.m_kappa(omega)
            return (1 + kappa * (1 - np.sqrt(T / Tc)))**2

    def _get_mixture_params(self, T, fractions, kij):
        """Calculate mixture parameters am and bm."""
        a_i = np.array([self.a_pure_params[c] * self._get_alpha(T, c) for c in self.components])
        b_i = np.array([self.b_pure_params[c] for c in self.components])

        bm = np.sum(fractions * b_i)
        am = 0.0
        for i in range(len(self.components)):
            for j in range(len(self.components)):
                k_val = kij if i != j else 0
                am += fractions[i] * fractions[j] * np.sqrt(a_i[i] * a_i[j]) * (1 - k_val)
        return am, bm

    def _solve_eos_for_Z(self, am, bm, P, T):
        A = am * P / (self.R**2 * T**2)
        B = bm * P / (self.R * T)

        if self.eos_name == 'redlich-kwong':
            coeffs = [1, -1, A - B - B**2, -A * B]
        else:
            coeffs = [1, -(1 - B), (A - 3*B**2 - 2*B), -(A*B - B**2 - B**3)]

        roots = np.roots(coeffs)
        real_roots = roots[np.isreal(roots)].real
        if len(real_roots) == 0:
            return np.nan, np.nan
        return min(real_roots), max(real_roots)

    def _get_fugacity_coeffs(self, Z, am, bm, P, T, fractions, kij):
        """Calculate fugacity coefficients for each component."""
        if am < 0 or (Z - (bm * P / (self.R * T))) <= 1e-12:
            return np.full_like(fractions, np.nan)

        A = am * P / (self.R**2 * T**2)
        B = bm * P / (self.R * T)
        a_i = np.array([self.a_pure_params[c] * self._get_alpha(T, c) for c in self.components])
        b_i = np.array([self.b_pure_params[c] for c in self.components])
        
        sum_term = np.zeros_like(fractions)
        for i in range(len(self.components)):
            for j in range(len(self.components)):
                k_val = kij if i != j else 0
                a_ij = np.sqrt(a_i[i] * a_i[j]) * (1-k_val)
                sum_term[i] += fractions[j] * a_ij

        log_arg = (Z + self.delta1 * B) / (Z + self.delta2 * B)
        if log_arg <= 1e-12:
            return np.full_like(fractions, np.nan)
        
        log_phi = (b_i / bm) * (Z - 1) - np.log(Z - B) - (A / (B * (self.delta1 - self.delta2))) * \
                  ((2 * sum_term / am) - (b_i / bm)) * np.log(log_arg)
        return np.exp(log_phi)

    def _get_eos_params_pyo(self, T, fractions, kij, P):
        """Calculate EOS parameters am, bm, A, B using Pyomo expressions."""
        a_i = [self.a_pure_params[c] * self._get_alpha(T, c) for c in self.components]
        b_i = [self.b_pure_params[c] for c in self.components]

        bm = sum(fractions[i] * b_i[i] for i in range(len(self.components)))
        am = 0.0
        for i in range(len(self.components)):
            for j in range(len(self.components)):
                k_val = kij if i != j else 0.0
                am += fractions[i] * fractions[j] * pyo.sqrt(a_i[i] * a_i[j]) * (1 - k_val)

        A = am * P / (self.R**2 * T**2)
        B = bm * P / (self.R * T)
        return am, bm, A, B

    def _get_log_phi_pyo(self, Z, am, bm, A, B, T, fractions, kij):
        a_i = [self.a_pure_params[c] * self._get_alpha(T, c) for c in self.components]
        b_i = [self.b_pure_params[c] for c in self.components]

        sum_term = [0.0] * len(self.components)
        for i in range(len(self.components)):
            for j in range(len(self.components)):
                k_val = kij if i != j else 0.0
                a_ij = pyo.sqrt(a_i[i] * a_i[j]) * (1 - k_val)
                sum_term[i] += fractions[j] * a_ij

        log_phi_list = []
        if self.eos_name == 'redlich-kwong':
            for i in range(len(self.components)):
                bi = b_i[i]
                term1 = bi / bm * (Z - 1) - pyo.log(Z - B)
                term2 = A / (B * pyo.sqrt(T)) * ((2 * sum_term[i] / am) - bi / bm) * pyo.log(1 + B / Z)
                log_phi_list.append(term1 - term2)
        else:
            log_arg = (Z + self.delta1 * B) / (Z + self.delta2 * B)
            term3_factor_stable = (am / (bm * self.R * T * (self.delta1 - self.delta2))) * pyo.log(log_arg)
            for i in range(len(self.components)):
                term1 = (b_i[i] / bm) * (Z - 1)
                term2 = pyo.log(Z - B)
                term3_inner = (2 * sum_term[i] / am) - (b_i[i] / bm)
                term3 = term3_factor_stable * term3_inner
                log_phi_list.append(term1 - term2 - term3)

        return log_phi_list

    def fit_kij(self, 
                experimental_data, 
                mode: str = 'isothermal'):
        
        if mode.lower() == 'isothermal':
            return self._fit_kij_isothermal(experimental_data)
        elif mode.lower() == 'isobaric':
            return self._fit_kij_isobaric(experimental_data)
        else:
            raise ValueError("Mode must be either 'isothermal' or 'isobaric'")

    def _fit_kij_isothermal(self, experimental_data):
        """Optimize kij for isothermal data (T constant, P varies)"""
        T_exp = experimental_data['T'].iloc[0]  # Constant temperature

        model = pyo.ConcreteModel()
        model.kij = pyo.Var(bounds=(-1, 1))  # Adicionei bounds para kij
        model.points = pyo.Set(initialize=experimental_data.index)

        # Initialize variables
        model.P_calc = pyo.Var(model.points, within=pyo.NonNegativeReals)
        model.y = pyo.Var(self.components, model.points, bounds=(0,1))
        model.Zl = pyo.Var(model.points, bounds=(0,2))
        model.Zv = pyo.Var(model.points, bounds=(0,2))

        # Initialize values
        for i in model.points:
            x_init = np.array([experimental_data.loc[i, 'x1'], 1-experimental_data.loc[i, 'x1']])
            y_init = np.array([experimental_data.loc[i, 'y1'], 1-experimental_data.loc[i, 'y1']])
            P_init = experimental_data.loc[i, 'P']
            
            model.P_calc[i].value = P_init
            for c in self.components:
                model.y[c,i].value = y_init[0] if c == self.components[0] else y_init[1]
            
            # Initialize Z values
            am_L, bm_L = self._get_mixture_params(T_exp, x_init, 0.0)
            zl, _ = self._solve_eos_for_Z(am_L, bm_L, P_init, T_exp)
            model.Zl[i].value = zl if np.isfinite(zl) else 0.1
            
            am_V, bm_V = self._get_mixture_params(T_exp, y_init, 0.0)
            _, zv = self._solve_eos_for_Z(am_V, bm_V, P_init, T_exp)
            model.Zv[i].value = zv if np.isfinite(zv) else 0.9

        # Objective function
        def obj_rule(m):
            error = sum(((m.P_calc[i] - experimental_data.loc[i, 'P']) / experimental_data.loc[i, 'P'])**2 
                       for i in m.points)
            return error + 1e-4 * m.kij**2  # Regularization
        model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

        # Constraints
        model.constraints = pyo.ConstraintList()
        for i in model.points:
            x = [experimental_data.loc[i, 'x1'], 1 - experimental_data.loc[i, 'x1']]
            y = [model.y[c, i] for c in self.components]

            # Sum of vapor fractions must be 1
            model.constraints.add(sum(y) == 1.0)

            # Liquid phase EOS
            am_L, bm_L, A_L, B_L = self._get_eos_params_pyo(T_exp, x, model.kij, model.P_calc[i])
            model.constraints.add(model.Zl[i]**3 - (1 - B_L)*model.Zl[i]**2 +
                                (A_L - 3*B_L**2 - 2*B_L)*model.Zl[i] -
                                (A_L*B_L - B_L**2 - B_L**3) == 0)

            # Vapor phase EOS
            am_V, bm_V, A_V, B_V = self._get_eos_params_pyo(T_exp, y, model.kij, model.P_calc[i])
            model.constraints.add(model.Zv[i]**3 - (1 - B_V)*model.Zv[i]**2 +
                                (A_V - 3*B_V**2 - 2*B_V)*model.Zv[i] -
                                (A_V*B_V - B_V**2 - B_V**3) == 0)
            
            # Physical bounds for Z
            model.constraints.add(model.Zl[i] >= B_L + 1e-6)
            model.constraints.add(model.Zv[i] >= B_V + 1e-6)

            # Fugacity equality
            log_phi_L = self._get_log_phi_pyo(model.Zl[i], am_L, bm_L, A_L, B_L, T_exp, x, model.kij)
            log_phi_V = self._get_log_phi_pyo(model.Zv[i], am_V, bm_V, A_V, B_V, T_exp, y, model.kij)
            
            for j in range(len(self.components)):
                if x[j] > 1e-6:
                    model.constraints.add(pyo.exp(log_phi_L[j]) * x[j] == pyo.exp(log_phi_V[j]) * y[j])

        # Solver
        solver = get_ipopt_solver()
        solver.options = {
            'tol': 1e-6,
            'max_iter': 1000,
            'bound_push': 1e-8,
            'nlp_scaling_method': 'gradient-based'
        }

        results = solver.solve(model, tee=False)
        
        if str(results.solver.termination_condition) == 'optimal':
            return pyo.value(model.kij)
        else:
            print("Warning: Optimization did not converge perfectly")
            return pyo.value(model.kij) if hasattr(model.kij, 'value') else 0.0

    def _fit_kij_isobaric(self, experimental_data):
        """Optimize kij for isobaric data (P constant, T varies)"""
        P_exp = experimental_data['P'].iloc[0]  # Constant pressure

        model = pyo.ConcreteModel()
        model.kij = pyo.Var(bounds=(-1, 1))
        model.points = pyo.Set(initialize=experimental_data.index)

        # Initialize variables
        model.T_calc = pyo.Var(model.points, within=pyo.NonNegativeReals)
        model.y = pyo.Var(self.components, model.points, bounds=(0,1))
        model.Zl = pyo.Var(bounds=(0,2))
        model.Zv = pyo.Var(bounds=(0,2))

        # Initialize values
        for i in model.points:
            T_init = experimental_data.loc[i, 'T']
            x_init = np.array([experimental_data.loc[i, 'x1'], 1-experimental_data.loc[i, 'x1']])
            y_init = np.array([experimental_data.loc[i, 'y1'], 1-experimental_data.loc[i, 'y1']])
            
            model.T_calc[i].value = T_init
            for c in self.components:
                model.y[c,i].value = y_init[0] if c == self.components[0] else y_init[1]

        # Objective function
        def obj_rule(m):
            error = sum(((m.T_calc[i] - experimental_data.loc[i, 'T']) / experimental_data.loc[i, 'T'])**2 
                       for i in m.points)
            return error + 1e-4 * m.kij**2
        model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

        # Constraints
        model.constraints = pyo.ConstraintList()
        for i in model.points:
            x = [experimental_data.loc[i, 'x1'], 1 - experimental_data.loc[i, 'x1']]
            y = [model.y[c, i] for c in self.components]

            # Sum of vapor fractions must be 1
            model.constraints.add(sum(y) == 1.0)

            # Liquid phase EOS
            am_L, bm_L, A_L, B_L = self._get_eos_params_pyo(model.T_calc[i], x, model.kij, P_exp)
            model.constraints.add(model.Zl**3 - (1 - B_L)*model.Zl**2 +
                                (A_L - 3*B_L**2 - 2*B_L)*model.Zl -
                                (A_L*B_L - B_L**2 - B_L**3) == 0)

            # Vapor phase EOS
            am_V, bm_V, A_V, B_V = self._get_eos_params_pyo(model.T_calc[i], y, model.kij, P_exp)
            model.constraints.add(model.Zv**3 - (1 - B_V)*model.Zv**2 +
                                (A_V - 3*B_V**2 - 2*B_V)*model.Zv -
                                (A_V*B_V - B_V**2 - B_V**3) == 0)
            
            # Physical bounds for Z
            model.constraints.add(model.Zl >= B_L + 1e-6)
            model.constraints.add(model.Zv >= B_V + 1e-6)

            # Fugacity equality
            log_phi_L = self._get_log_phi_pyo(model.Zl, am_L, bm_L, A_L, B_L, model.T_calc[i], x, model.kij)
            log_phi_V = self._get_log_phi_pyo(model.Zv, am_V, bm_V, A_V, B_V, model.T_calc[i], y, model.kij)
            
            for j in range(len(self.components)):
                if x[j] > 1e-6:
                    model.constraints.add(pyo.exp(log_phi_L[j]) * x[j] == pyo.exp(log_phi_V[j]) * y[j])

        # Solver
        solver = get_ipopt_solver()
        solver.options = {
            'tol': 1e-6,
            'max_iter': 1000,
            'bound_push': 1e-8,
            'nlp_scaling_method': 'gradient-based'
        }

        results = solver.solve(model, tee=False)
        
        if str(results.solver.termination_condition) == 'optimal':
            return pyo.value(model.kij)
        else:
            print("Warning: Optimization did not converge perfectly")
            return pyo.value(model.kij) if hasattr(model.kij, 'value') else 0.0

    def run(self, experimental_data, mode='isothermal'):
        res = self.fit_kij(experimental_data, mode)
        return res