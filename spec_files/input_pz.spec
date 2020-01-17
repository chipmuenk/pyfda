# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files

hiddenimports = collect_submodules('scipy.signal')
datas = collect_data_files('scipy.signal')
excludes = collect_submodules('tornado') 
excludes += collect_submodules('colorama')
excludes += collect_submodules('sphinx')
excludes += collect_submodules('tkinter') 
excludes += collect_submodules('docutils')


a = Analysis(['pyfda/input_widgets/input_pz.py'],
             pathex=['pyfda/input_widgets'],
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

# Manually remove entire packages...
a.binaries = [x for x in a.binaries if not x[0].startswith("IPython")]
a.binaries = [x for x in a.binaries if not x[0].startswith("zmq")]

# Target remove specific ones...
#a.binaries = a.binaries - TOC([
#('sqlite3.dll', None, None)])
# ('tcl85.dll', None, None),
# ('tk85.dll', None, None),
# ('_sqlite3', None, None),
# ('_tkinter', None, None)])
 #('_ssl', None, None)

# Delete data...

a.datas = [x for x in a.datas if not x[0].startswith('tk')]
# os.path.dirname(x[1]).startswith("C:\\Python27\\Lib\\site-packages\\matplotlib")]

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          exclude_binaries=False,
          name='input_pz_exe',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='input_pz_dir')
