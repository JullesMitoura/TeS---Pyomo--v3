# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['main.py'],
             pathex=[r'C:\Users\jullesmitoura\Documents\TeS---Pyomo'],
             binaries=[
                 ('app/solver/bin/ipopt.exe', 'app/solver/bin'),
                 ('app/solver/bin/coinmumps-3.dll', 'app/solver/bin'),
                 ('app/solver/bin/ipopt-3.dll', 'app/solver/bin'),
                 ('app/solver/bin/ipoptamplinterface-3.dll', 'app/solver/bin'),
                 ('app/solver/bin/libifcoremd.dll', 'app/solver/bin'),
                 ('app/solver/bin/libiomp5md.dll', 'app/solver/bin'),
                 ('app/solver/bin/libmmd.dll', 'app/solver/bin'),
                 ('app/solver/bin/sipopt-3.dll', 'app/solver/bin'),
                 ('app/solver/bin/svml_dispmd.dll', 'app/solver/bin')
             ],
             datas=[
                 ('app', 'app'),
                 ('ico.ico', '.')
             ],
             hookspath=['.'],
             hiddenimports=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.datas,
          name='TeS_App',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True,
          icon='ico.ico')