from app.find_path import resource_path
import pyomo.environ as pyo

def get_ipopt_solver():
    try:
        solver = pyo.SolverFactory('ipopt')
        return solver
    except:
        solver = pyo.SolverFactory('ipopt', 
                                    executable = resource_path("app/solver/bin/ipopt.exe"))
        return solver