# -*- mode: python ; coding: utf-8 -*-

# https://realpython.com/pyinstaller-python/
# Pyinstaller cannot understand dynamic imports (hard enough for me ...) so all
# modules that are imported dynamically need to be added manually via "hiddenimports"
# https://techxmag.com/questions/how-to-add-dynamic-python-modules-to-pyinstallers-specs/

# How to choose between OpenBLAS and MKL optimized numpy / scipy: The MKL libraries increase
# size of the exe from ~80 MB to 350 MB under linux (and I haven't seen a speed gain)
# https://docs.anaconda.com/mkl-optimizations/
# This only works under Linux and OS X, under Windows there seems to be no feasible
# alternative to scipy built with mkl
# see:  https://stackoverflow.com/questions/46656367/how-to-create-an-environment-in-anaconda-with-numpy-nomkl

# Under windows, Qt library become installed twice, bloating the resulting exe
# This might be caused by pywin32 (Anaconda) and pypiwin32 both installed (or a similar
# issue related to Qt5)
# https://github.com/pyinstaller/pyinstaller/issues/1488

# Including an icon seems to be problem under windows. Some hints at
# https://stackoverflow.com/questions/45628653/add-ico-file-to-executable-in-pyinstaller

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

block_cipher = None
name_main = 'pyfdax'
path_main = 'pyfda'

from PyInstaller.utils.hooks import collect_submodules
## from PyInstaller.utils.hooks import collect_data_files

hiddenimports = []
datas = []

# add data (graphic and configuration files) as a list of tuples where the
# first tuple item is the file (full local path name) and the second the directory
# name in the pyinstaller archive
datas += [('pyfda/fixpoint_widgets/*.png', 'pyfda/fixpoint_widgets'),
    ('pyfda/fixpoint_widgets/fir_df/*.png', 'pyfda/fixpoint_widgets/fir_df'),
    ('pyfda/fixpoint_widgets/iir_df1/*.png', 'pyfda/fixpoint_widgets/iir_df1'),
    ('pyfda/libs/*.conf', 'pyfda/libs'),
    ('./*.md', '.'),
    ('pyfda/*.md', 'pyfda')]

# Add all json files from jschon package (used by amaranth) to datas. The directory
# specified in the second part of the datas tuple is only the jschon/... dir part, e.g.
# ('python3.10/site-packages/jschon/catalog/json-schema-2020-12/schema.json',
#  'jschon/catalog/json-schema-2020-12')
import os
import importlib
jschon_root = os.path.dirname(importlib.import_module('jschon').__file__)  # root dir for jschon package
json_files = [(os.path.join(root, name),
               os.path.join('jschon', root.partition('jschon' + os.sep)[2]))
                for root, dirs, files in os.walk(jschon_root)
                    for name in files
                        if name.endswith(".json")]
datas += json_files

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
    'pyfda.fixpoint_widgets.fir_df.fir_df_amaranth_ui',
    'pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp_ui']

excludes = []
# excludes += collect_submodules('amaranth')
excludes += collect_submodules('tornado')
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

# For MKL, set  binaries=[('/home/cmuenker/anaconda3/lib/libiomp5.so','.')],
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
	 # and not x[0].startswith('scipy/fftpack') # needed for windows
	 and not x[0].startswith('lib')
	 and not x[0].startswith('notebook'))]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

# name and content of the executable
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
          console=True,
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
