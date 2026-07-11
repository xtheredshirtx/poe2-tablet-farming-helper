"""Build a Windows release ZIP with PyInstaller.

Run from the repository root:
    python tools/build_windows_release.py

The output ZIP contains POE2TabletFarmingHelper.exe plus its bundled runtime
folder. Users should extract the ZIP and run the EXE.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "POE2TabletFarmingHelper"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
ARTIFACT_DIR = ROOT / "release_artifacts"


def app_version() -> str:
    with open(ROOT / "data" / "meta.json", encoding="utf-8") as f:
        return json.load(f)["app_version"]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    ARTIFACT_DIR.mkdir(exist_ok=True)
    for path in (DIST_DIR, BUILD_DIR, ROOT / f"{APP_NAME}.spec"):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        APP_NAME,
        "--add-data",
        f"{ROOT / 'data'};data",
        "--exclude-module",
        "PySide6.QtWebEngineWidgets",
        "--exclude-module",
        "PySide6.QtWebEngineCore",
        "--exclude-module",
        "PySide6.QtWebEngineQuick",
        str(ROOT / "main.py"),
    ])

    package_dir = DIST_DIR / APP_NAME
    if not (package_dir / f"{APP_NAME}.exe").exists():
        raise SystemExit(f"Missing built EXE: {package_dir / (APP_NAME + '.exe')}")

    version = app_version()
    zip_base = ARTIFACT_DIR / f"{APP_NAME}-v{version}-windows"
    zip_path = Path(shutil.make_archive(str(zip_base), "zip", root_dir=DIST_DIR, base_dir=APP_NAME))
    print(f"\nBuilt {zip_path}")


if __name__ == "__main__":
    main()
