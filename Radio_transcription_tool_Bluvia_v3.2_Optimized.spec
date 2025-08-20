# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['radio_transcription_final_build_clean.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Bluvia images', 'Bluvia images'),  # Include Bluvia images folder
    ],
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageTk',  # Essential for images
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox',  # GUI essentials
        'pydub', 'openai', 'threading', 'time', 'os', 'sys',  # Core functionality
        'httpx', 'httpx._client', 'httpx._types', 'httpx._utils',  # OpenAI dependency
        'tiktoken', 'aiohttp', 'websockets'  # Additional OpenAI dependencies
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
        'requests', 'urllib3',  # Keep httpx, remove others

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
        'selenium', 'beautifulsoup4', 'lxml'
    ],
    noarchive=False,
    optimize=0,
)

# Filter out heavy binaries
a.binaries = [x for x in a.binaries if not any(exclude in x[0].lower() for exclude in [
    'nltk', 'keybert', 'torch', 'tensorflow', 'sklearn', 'scipy',
    'matplotlib', 'seaborn', 'plotly', 'bokeh', 'dash', 'flask',
    'django', 'fastapi', 'sqlalchemy', 'sqlite', 'postgres', 'mysql',
    'mongo', 'redis', 'elasticsearch', 'selenium', 'beautifulsoup',
    'lxml', 'jupyter', 'ipython', 'pytest', 'unittest', 'coverage'
])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Radio_transcription_tool_Bluvia_v3.2_Optimized',
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
    icon='Bluvia images\\Bluebird app icon 2a.ico',  # Double backslashes for Windows
)

