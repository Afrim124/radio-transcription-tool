# -*- mode: python ; coding: utf-8 -*-
import os

# Get current directory for absolute paths
current_dir = os.getcwd()

a = Analysis(
    ['main.py'],  # Entry point
    pathex=[current_dir],
    binaries=[],
    datas=[
        # Include all modular Python files
        ('config.py', '.'),
        ('logging_config.py', '.'),
        ('phrase_filtering.py', '.'),
        ('transcription.py', '.'),
        ('utils.py', '.'),
        ('gui.py', '.'),
        ('audio_processing.py', '.'),
        ('app.py', '.'),
        
        # Include Bluvia images folder
        ('Bluvia images', 'Bluvia images'),
    ],
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageTk',  # Essential for images
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox',  # GUI essentials
        'pydub', 'openai', 'threading', 'time', 'os', 'sys',  # Core functionality
        'httpx', 'httpx._client', 'httpx._types', 'httpx._utils',  # OpenAI dependency
        'tiktoken', 'aiohttp', 'websockets',  # Additional OpenAI dependencies
        'requests', 'urllib3', 'bs4', 'beautifulsoup4',  # Web scraping dependencies
        
        # Include modular imports
        'config', 'logging_config', 'phrase_filtering', 'transcription', 'utils', 'gui',
        
        # Collections for phrase processing
        'collections', 'collections.Counter',
        
        # Additional modules that might be imported
        'shutil', 'math', 'webbrowser', 'subprocess'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy ML packages
        'keybert', 'sentence_transformers', 'transformers',
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'keras', 'sklearn', 'scipy',
        'matplotlib', 'seaborn', 'plotly', 'bokeh',
        'nltk', 'spacy', 'gensim',

        # Exclude web frameworks (but keep httpx for OpenAI)
        'flask', 'django', 'fastapi', 'aiohttp',
        # Keep httpx, requests, urllib3 for web functionality

        # Exclude database packages
        'sqlalchemy', 'sqlite3', 'psycopg2', 'mysql',
        'pymongo', 'redis', 'elasticsearch',

        # Exclude development tools
        'pytest', 'unittest', 'coverage', 'black',
        'flake8', 'mypy', 'jupyter', 'ipython',

        # Exclude scientific packages
        'numpy', 'pandas', 'scipy', 'sympy',
        'networkx', 'scikit-image', 'opencv',

        # Exclude other heavy packages
        'selenium'
    ],
    noarchive=False,
    optimize=0,
)

# Filter out heavy binaries and exclude FFmpeg binaries
a.binaries = [x for x in a.binaries if not any(exclude in x[0].lower() for exclude in [
    'nltk', 'keybert', 'torch', 'tensorflow', 'sklearn', 'scipy',
    'matplotlib', 'seaborn', 'plotly', 'bokeh', 'dash', 'flask',
    'django', 'fastapi', 'sqlalchemy', 'sqlite', 'postgres', 'mysql',
    'mongo', 'redis', 'elasticsearch', 'selenium',
    'jupyter', 'ipython', 'pytest', 'unittest', 'coverage',
    'ffmpeg', 'ffplay', 'bin'  # Exclude FFmpeg binaries and bin directory
])]

# Filter out datas to exclude bin directory and FFmpeg files
a.datas = [x for x in a.datas if not any(exclude in x[0].lower() for exclude in [
    'bin', 'ffmpeg', 'ffplay'  # Exclude bin directory and FFmpeg files
])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Radio_transcription_tool_Bluvia_v3.7_Modular',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Bluvia images\\Bluebird app icon 2a.ico',  # Use relative path for icon
)


