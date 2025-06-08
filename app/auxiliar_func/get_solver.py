from app.find_path import resource_path
import pyomo.environ as pyo

def get_ipopt_solver():
    try:
        solver = pyo.SolverFactory('ipopt', 
                                   executable=resource_path("app/solver/bin/ipopt.exe"))
        if not solver.available():
            raise RuntimeError("IPOPT não está disponível no caminho especificado.")
    except Exception:
        solver = pyo.SolverFactory('ipopt')
    return solver