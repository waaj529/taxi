# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[('core', 'core'), ('ui', 'ui'), ('translations', 'translations'), ('assets', 'assets'), ('ride_guardian.db', '.'), ('hhh.xlsx', '.'), ('ride_guardian_test_data.xlsx', '.'), ('Fahrtenbuch_2025-06-01_2025-06-03.xlsx', '.'), ('translations/ride_guardian_de.qm', 'translations'), ('translations/ride_guardian_de.ts', 'translations')],
             hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtPrintSupport', 'PyQt6.QtSvg', 'PyQt6.QtCharts', 'pandas', 'numpy', 'openpyxl', 'reportlab', 'matplotlib', 'matplotlib.backends.backend_qt5agg', 'matplotlib.backends.backend_agg', 'PIL', 'PIL._tkinter_finder', 'requests', 'sqlite3', 'core.database', 'core.translation_manager', 'core.company_manager', 'ui.views', 'ui.components', 'ui.widgets'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['tkinter', 'matplotlib.tests', 'pandas.tests', 'numpy.tests', 'test', 'tests', 'setuptools', 'pip', 'wheel'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='RideGuardian-Main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='assets/ride_guardian_icon.ico',
          version_file='version_info.txt')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='RideGuardian-Main')
