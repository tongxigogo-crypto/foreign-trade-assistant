# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path.cwd()
datas = [
    (str(project_root / "app" / "dashboard_ui.html"), "app"),
    (str(project_root / "app" / "dashboard_layout_v2.json"), "app"),
]

a = Analysis(
    [str(project_root / "app" / "tray_entry.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "pystray",
        "pystray._base",
        "pystray._win32",
        "pystray._darwin",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="InVault",
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
