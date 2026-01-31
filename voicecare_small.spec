# -*- mode: python ; coding: utf-8 -*-
# VoiceCare Small Model - PyInstaller Spec with Vosk DLL support

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, get_module_file_attribute

# Get the virtual environment's site-packages directory
venv_path = os.path.dirname(sys.executable)
if venv_path.endswith('Scripts'):
    venv_site_packages = os.path.join(os.path.dirname(venv_path), 'Lib', 'site-packages')
else:
    venv_site_packages = os.path.join(sys.base_prefix, 'Lib', 'site-packages')

vosk_path = os.path.join(venv_site_packages, 'vosk')

a = Analysis(
    ['Small Model\\voicecare_frontend.py'],
    pathex=[],
    binaries=[
        # Include Vosk native libraries from virtual environment
        (vosk_path, 'vosk'),
    ],
    datas=[
        # Include Vosk model data
        ('vosk\\vosk-model-small-en-us-0.15', 'vosk/vosk-model-small-en-us-0.15'),
    ],
    hiddenimports=[
        'vosk',
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
    name='VoiceCare',
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
    name='VoiceCare',
)
