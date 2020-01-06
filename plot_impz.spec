# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files

hiddenimports = collect_submodules('scipy.signal')
datas = collect_data_files('scipy.signal')
excludes = collect_submodules('tornado') 
excludes += collect_submodules('colorama')
excludes += collect_submodules('tkinter') 
excludes += collect_submodules('docutils')


a = Analysis(['pyfda\\plot_widgets\\plot_impz.py'],
             pathex=['pyfda/plot_widgets', 'D:\\Daten\\design\\python\\git\\pyfda'],
             binaries=[],
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=['hook-pyfda.plot_widgets.py'],
             excludes=excludes,
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
          name='plot_impz',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='plot_impz')
