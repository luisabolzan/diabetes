# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('nutrition5k_model_rgb.pth', '.'),  # Bundle the model file
        ('src', 'src'),                      # Bundle the source code
        ('C:\\Users\\lulrb\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\nicegui', 'nicegui') # NiceGUI assets
    ],
    hiddenimports=['uvicorn', 'nicegui', 'sqlalchemy', 'cv2', 'torch', 'torchvision', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DiabetesCalculator',
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
)
