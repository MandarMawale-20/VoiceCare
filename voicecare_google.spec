# -*- mode: python ; coding: utf-8 -*-
# VoiceCare Google Speech Recognition Edition - PyInstaller Spec

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, get_module_file_attribute

# Get the virtual environment's site-packages directory
venv_path = os.path.dirname(sys.executable)
if venv_path.endswith('Scripts'):
    venv_site_packages = os.path.join(os.path.dirname(venv_path), 'Lib', 'site-packages')
else:
    venv_site_packages = os.path.join(sys.base_prefix, 'Lib', 'site-packages')

a = Analysis(
    ['GoogleSpeech recognition\\voiceCare_frontend.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'google',
        'google.cloud',
        'google.cloud.speech',
        'pyaudio',
        'pyttsx3',
        'apscheduler',
        'langdetect',
        'pygame',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tkinter',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VoiceCareGoogle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='VoiceCareGoogle',
)
