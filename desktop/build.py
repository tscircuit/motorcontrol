"""Build from the repository root with the host Python and PyInstaller."""
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "build" / "desktop"

args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--name", "Motorcontrol Desktop", "--distpath", str(OUT),
        "--workpath", str(OUT / "work"), "--specpath", str(OUT / "spec"),
        "--windowed", "--onefile" if os.name == "nt" else "--onedir"]
if sys.platform == "darwin":
    args += ["--osx-bundle-identifier", "com.tscircuit.motorcontrol", "--icon", str(HERE / "icon.icns")]
elif os.name == "nt":
    args += ["--icon", str(HERE / "icon.ico")]
for source, dest in [(ROOT / "dist", "dist"), (HERE / "images", "images"), (HERE / "ui", "ui")]:
    args += ["--add-data", f"{source}{os.pathsep}{dest}"]
subprocess.run([*args, str(HERE / "motorcontrol.py")], check=True)
