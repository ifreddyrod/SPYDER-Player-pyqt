# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect VLC plugins and data files
vlc_plugin_path = None

# Try common VLC installation paths
possible_paths = [
    os.path.join(os.environ.get('PROGRAMFILES', ''), 'VideoLAN', 'VLC', 'plugins'),
    os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'VideoLAN', 'VLC', 'plugins'),
    '/usr/lib/vlc/plugins',  # Linux path
    '/usr/local/lib/vlc/plugins'  # macOS path
]

for path in possible_paths:
    if os.path.exists(path):
        vlc_plugin_path = path
        break

if vlc_plugin_path is None:
    raise Exception("Could not find VLC plugins directory")

# Collect all VLC plugins
vlc_plugins = []
for root, dirs, files in os.walk(vlc_plugin_path):
    for file in files:
        if file.endswith('.dll') or file.endswith('.so'):
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, vlc_plugin_path)
            vlc_plugins.append((full_path, f'plugins/{relative_path}'))

# Add assets folder to datas
assets_path = os.path.join('assets', 'icons')
icon_file = os.path.join(assets_path, 'spider_dark_icon.ico')

a = Analysis(
    ['SpyderPlayerApp.py'],  
    pathex=[],
    binaries=vlc_plugins,
    datas=[(assets_path, 'assets/icons')],  # Include the assets folder
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'm3u_parser', 'pydantic'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SpyderPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file  # Add the icon file
)