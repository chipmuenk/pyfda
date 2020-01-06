# -*- mode: python ; coding: utf-8 -*-

# https://techxmag.com/questions/how-to-add-dynamic-python-modules-to-pyinstallers-specs/

block_cipher = None

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files

hiddenimports = collect_submodules('scipy.signal')
hiddenimports += [
    'pyfda.input_widgets.input_specs','pyfda.input_widgets.input_coeffs',
    'pyfda.input_widgets.input_pz','pyfda.input_widgets.input_info',
    'pyfda.input_widgets.input_files','pyfda.input_widgets.input_fixpoint_specs']
hiddenimports += [
    'pyfda.filter_designs.equiripple','pyfda.filter_designs.firwin','pyfda.filter_designs.ma',
    'pyfda.filter_designs.equiripple','pyfda.filter_designs.butterworth','pyfda.filter_designs.ellip',
    'pyfda.filter_designs.cheby1','pyfda.filter_designs.cheby2'
    ] 
hiddenimports += [
    'pyfda.fixpoint_widgets.fir_df','pyfda.fixpoint_widgets.delay1']
    
datas  = collect_data_files('scipy.signal')

a = Analysis(['pyfda\\input_widgets\\input_tab_widgets.py'],
             pathex=['D:\\Daten\\design\\python\\git\\pyfda'],
             binaries=[],
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
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
          a.zipfiles,
          a.datas,
          [],
          name='input_tab_widgets',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
