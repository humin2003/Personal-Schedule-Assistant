# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None

# --- [FIX QUAN TRỌNG] ---
# Copy metadata của Streamlit để tránh lỗi "PackageNotFoundError"
datas = []
datas += copy_metadata('streamlit')  # <--- Dòng này sửa lỗi của bạn
datas += copy_metadata('click')      # Streamlit dùng click, copy luôn cho chắc
datas += copy_metadata('tqdm')
datas += copy_metadata('regex')
datas += copy_metadata('requests')
datas += copy_metadata('packaging')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')

# Thu thập file tĩnh của Streamlit & Calendar
datas += collect_data_files('streamlit')
datas += collect_data_files('streamlit_calendar')
datas += collect_data_files('underthesea')

# Thêm code nguồn của bạn
datas += [
    ('src', 'src'),
    ('data', 'data'),
    ('tests', 'tests'),
]

# Thu thập các module ẩn
hiddenimports = [
    'streamlit',
    'pandas',
    'underthesea',
    'winotify',
    'plyer',
    'plyer.platforms.win.notification',
    'sqlite3',
    'babel.numbers', # Lỗi thường gặp với streamlit-calendar
]
hiddenimports += collect_submodules('streamlit')
hiddenimports += collect_submodules('underthesea')
hiddenimports += collect_submodules('streamlit_calendar')

a = Analysis(
    ['run_executable.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='ScheduleAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Vẫn để True để xem có lỗi gì khác không
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)