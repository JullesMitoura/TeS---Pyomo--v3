from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Captura TODOS os submódulos do Pyomo
hiddenimports = collect_submodules('pyomo')

# Inclui módulos específicos que podem ser problemáticos
hiddenimports += [
    'pyomo.dataportal.plugins',
    'pyomo.dataportal.plugins.csv',
    'pyomo.dataportal.plugins.sql',
    'pyomo.opt.plugins.solvers',
    'pyomo.solvers.plugins'
]

# Inclui arquivos de dados do Pyomo
datas = collect_data_files('pyomo')