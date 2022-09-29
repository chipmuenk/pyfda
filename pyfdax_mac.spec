# -*- mode: python ; coding: utf-8 -*-

# https://realpython.com/pyinstaller-python/
# Pyinstaller cannot understand dynamic imports (hard enough for me ...) so all
# modules that are imported dynamically need to be added manually via "hiddenimports"
# https://techxmag.com/questions/how-to-add-dynamic-python-modules-to-pyinstallers-specs/

# How to choose between OpenBLAS and MKL optimized numpy / scipy: The MKL libraries increase
# size of the exe from ~80 MB to 350 MB under linux (and I haven't seen a speed gain)
# https://docs.anaconda.com/mkl-optimizations/

# Including an icon and other Mac-related stuff is described in
# https://www.pythonguis.com/tutorials/packaging-pyqt5-applications-pyinstaller-macos-dmg/

# check also https://github.com/actions/upload-release-asset/issues/35

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

block_cipher = None
name_main = 'pyfdax_osx'
path_main = 'pyfda_osx'

from PyInstaller.utils.hooks import collect_submodules
## from PyInstaller.utils.hooks import collect_data_files

hiddenimports = []
datas = []
#hiddenimports = collect_submodules('scipy.signal')
#datas += collect_data_files('scipy.signal')
## datas += collect_data_files('scipy.fftpack') # windows only? Adds some *.py files

# add images and configuration files
datas += [('pyfda/fixpoint_widgets/*.png', 'pyfda/fixpoint_widgets'),
    ('pyfda/fixpoint_widgets/fir_df/*.png', 'pyfda/fixpoint_widgets/fir_df'),
    ('pyfda/fixpoint_widgets/iir_df1/*.png', 'pyfda/fixpoint_widgets/iir_df1'),
    ('pyfda/libs/*.conf', 'pyfda/libs'),
    ('./*.md', '.'),
    ('pyfda/*.md', 'pyfda')]

## hiddenimports += ['html.parser'] # needed for markdown 3.3 compatibility
## hiddenimports += ['scipy.special.cython_special']
### Plot Widgets
hiddenimports += [
    'pyfda.plot_widgets.plot_hf','pyfda.plot_widgets.plot_phi','pyfda.plot_widgets.plot_tau_g',
    'pyfda.plot_widgets.plot_pz','pyfda.plot_widgets.plot_impz','pyfda.plot_widgets.plot_3d']
### Input Widgets
hiddenimports += [
    'pyfda.input_widgets.input_specs','pyfda.input_widgets.input_coeffs',
    'pyfda.input_widgets.input_pz','pyfda.input_widgets.input_info',
    'pyfda.input_widgets.input_fixpoint_specs']
### Filter Designs
hiddenimports += [
    'pyfda.filter_widgets.equiripple','pyfda.filter_widgets.firwin','pyfda.filter_widgets.ma',
    'pyfda.filter_widgets.bessel','pyfda.filter_widgets.butter','pyfda.filter_widgets.ellip',
    'pyfda.filter_widgets.cheby1','pyfda.filter_widgets.cheby2',
	'pyfda.filter_widgets.manual'] 
### Fixpoint Widgets
hiddenimports += [
    'pyfda.fixpoint_widgets.fir_df.fir_df_pyfixp_ui',
    'pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp_ui']

excludes  = collect_submodules('tornado') 
excludes += collect_submodules('colorama')
excludes += collect_submodules('tkinter') 
excludes += collect_submodules('jedi')
# excludes += collect_submodules('PIL')
excludes += collect_submodules('nbconvert')
excludes += collect_submodules('nbformat')
#excludes += collect_submodules('scipy.optimize') # needed
#excludes += collect_submodules('scipy.sparse') # needed
#excludes += collect_submodules('scipy.ndimage') # needed
#jupyter,scipy.spatial, scipy.stats, scipy.integrate, scipy.interpolate

a = Analysis(['pyfda/pyfdax.py'],
             pathex=[],
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

# Manually remove entire packages...
## a.binaries = [x for x in a.binaries if not x[0].startswith("IPython")] # no effect
## a.binaries = [x for x in a.binaries if not x[0].startswith("zmq")] # no effect

# Remove specific libraries ...
a.binaries = a.binaries - TOC([
 ('sqlite3.dll', None, None),
 ('tcl85.dll', None, None),
 ('tk85.dll', None, None),
 ('_sqlite3', None, None),
 ('_tkinter', None, None),
 ('Qt5Qml.dll', None, None),
 ('libQt5Qml.so.5', None, None),
 ('libQt5Quick.so.5', None, None),
 #('libstdc++.so.6', None, None),
 ('libzmq.so.5', None, None),
 ('libsqlite3.so.0', None, None)
 # ('opengl32sw.dll', None, None) # need to test
    ])
 # ('_ssl', None, None), # needed for?
 # libicudata.so.58' # central Qt library 
 # libQt5Svg.so.5' # needed for icons


# Delete data ...
a.datas = [x for x in a.datas if 
	(not x[0].startswith('tk')
	 and not x[0].startswith('IPython')
	 and not x[0].startswith('lib')
	 and not x[0].startswith('notebook'))]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

# name and content of the executable in the bundle file
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name=name_main,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
     	  icon=None)
    # icon is set in main program via qrc resources, no import needed

# directory name and its content for files to be collected
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name=name_main + '_dir')

# name and content of bundled file -> the actual app file
app = BUNDLE(coll,
             name=name_main +'.app',
             icon=None,
             bundle_identifier=None)
