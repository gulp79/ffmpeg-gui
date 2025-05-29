#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurazione per il deployment e la distribuzione di FFmpeg GUI
"""

import os
import sys
from pathlib import Path

# Informazioni applicazione
APP_NAME = "FFmpeg GUI"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Gulp79"
APP_DESCRIPTION = "Interfaccia grafica moderna per FFmpeg"
APP_URL = "https://github.com/gulp79/ffmpeg-gui"

# Configurazioni PyInstaller
PYINSTALLER_CONFIG = {
    'name': 'FFmpeg_GUI',
    'onefile': True,
    'windowed': True,  # Nasconde console su Windows
    'icon': 'assets/icon.ico',  # Percorso icona (opzionale)
    'add_data': [
        # Aggiungi file aggiuntivi se necessario
        # ('path/to/source', 'path/to/dest')
    ],
    'hidden_imports': [
        'customtkinter',
        'PIL._tkinter_finder',
        'queue',
        'threading',
        'subprocess',
        'pathlib',
        'shutil',
        'signal'
    ],
    'exclude_modules': [
        'matplotlib',
        'numpy',
        'pandas',
        'scipy'
    ]
}

# Configurazioni per diverse piattaforme
PLATFORM_CONFIG = {
    'windows': {
        'executable_name': 'FFmpeg_GUI.exe',
        'installer_name': f'FFmpeg_GUI_Setup_{APP_VERSION}.exe',
        'portable_name': f'FFmpeg_GUI_Portable_{APP_VERSION}.zip',
        'requirements': [
            'Windows 10 or higher',
            'NVIDIA GPU with CUDA support (recommended)',
            'FFmpeg in PATH or local folder'
        ]
    },
    'linux': {
        'executable_name': 'ffmpeg_gui',
        'package_name': f'ffmpeg-gui_{APP_VERSION}_amd64.deb',
        'archive_name': f'FFmpeg_GUI_Linux_{APP_VERSION}.tar.gz',
        'requirements': [
            'Linux with GTK3 support',
            'FFmpeg installed via package manager',
            'NVIDIA drivers for CUDA (optional)'
        ]
    },
    'macos': {
        'executable_name': 'FFmpeg GUI.app',
        'dmg_name': f'FFmpeg_GUI_{APP_VERSION}.dmg',
        'requirements': [
            'macOS 10.14 or higher',
            'FFmpeg via Homebrew or MacPorts',
            'Xcode Command Line Tools'
        ]
    }
}

# Script per creazione release automatica
def create_release_info():
    """Crea informazioni per la release"""
    platform = sys.platform.lower()
    
    if 'win' in platform:
        config = PLATFORM_CONFIG['windows']
    elif 'linux' in platform:
        config = PLATFORM_CONFIG['linux']
    elif 'darwin' in platform:
        config = PLATFORM_CONFIG['macos']
    else:
        config = PLATFORM_CONFIG['linux']  # Default
    
    release_info = {
        'version': APP_VERSION,
        'platform': platform,
        'executable': config['executable_name'],
        'requirements': config['requirements'],
        'build_command': generate_build_command(),
        'test_command': generate_test_command()
    }
    
    return release_info

def generate_build_command():
    """Genera comando di build per PyInstaller"""
    cmd_parts = ['pyinstaller']
    
    if PYINSTALLER_CONFIG['onefile']:
        cmd_parts.append('--onefile')
    
    if PYINSTALLER_CONFIG['windowed']:
        cmd_parts.append('--windowed')
    
    cmd_parts.extend(['--name', PYINSTALLER_CONFIG['name']])
    
    if PYINSTALLER_CONFIG.get('icon'):
        cmd_parts.extend(['--icon', PYINSTALLER_CONFIG['icon']])
    
    for module in PYINSTALLER_CONFIG['hidden_imports']:
        cmd_parts.extend(['--hidden-import', module])
    
    for module in PYINSTALLER_CONFIG['exclude_modules']:
        cmd_parts.extend(['--exclude-module', module])
    
    cmd_parts.append('ffmpeg_gui.py')
    
    return ' '.join(cmd_parts)

def generate_test_command():
    """Genera comando di test"""
    return 'python -m pytest tests/ -v' if Path('tests').exists() else 'python FFmpeg-GUI.py --test'

# Configurazione GitHub Actions
GITHUB_ACTIONS_CONFIG = {
    'python_versions': ['3.8', '3.9', '3.10', '3.11'],
    'os_matrix': ['windows-latest', 'ubuntu-latest', 'macos-latest'],
    'build_platforms': ['windows', 'linux'],  # macOS da aggiungere se necessario
    'release_assets': {
        'windows': [
            'FFmpeg_GUI_Windows_Portable_{version}.zip',
            'FFmpeg_GUI_Windows_Installer_{version}.zip'
        ],
        'linux': [
            'FFmpeg_GUI_Linux_{version}.tar.gz'
        ]
    }
}

if __name__ == '__main__':
    """Test della configurazione"""
    import json
    
    print(f"=== {APP_NAME} v{APP_VERSION} ===")
    print(f"Configurazione deployment per: {sys.platform}")
    print()
    
    release_info = create_release_info()
    print("Release Info:")
    print(json.dumps(release_info, indent=2))
    print()
    
    print("Build Command:")
    print(release_info['build_command'])
    print()
    
    print("Test Command:")
    print(release_info['test_command'])
    print()
    
    print("PyInstaller Config:")
    print(json.dumps(PYINSTALLER_CONFIG, indent=2))
