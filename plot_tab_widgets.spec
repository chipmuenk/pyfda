# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files

hiddenimports = collect_submodules('scipy.signal')
hiddenimports += [
    'pyfda.plot_widgets.plot_hf','pyfda.plot_widgets.plot_phi','pyfda.plot_widgets.plot_tau_g',
    'pyfda.plot_widgets.plot_pz','pyfda.plot_widgets.plot_3d']
datas = collect_data_files('scipy.signal')
excludes = collect_submodules('tornado') 
excludes += collect_submodules('colorama')
excludes += collect_submodules('tkinter') 
excludes += collect_submodules('docutils')

a = Analysis(['pyfda\\plot_widgets\\plot_tab_widgets.py'],
             pathex=['D:\\Daten\\design\\python\\git\\pyfda'],
             binaries=[],
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='plot_tab_widgets',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
