from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path


def output_name() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "mid_native.dll"
    if system == "darwin":
        return "libmid_native.dylib"
    return "libmid_native.so"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the optional C++17 lag-matrix kernel")
    parser.add_argument("--compiler", default=None, help="Override C++ compiler executable")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source = root / "cpp" / "lagged_design.cpp"
    out_dir = root / "build" / "native"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / output_name()

    system = platform.system().lower()
    if system == "windows":
        compiler = args.compiler or shutil.which("cl")
        if not compiler:
            raise SystemExit(
                "MSVC `cl` was not found. Use a Developer PowerShell or pass --compiler. "
                "The Python backend remains fully supported without C++."
            )
        cmd = [compiler, "/std:c++17", "/O2", "/LD", str(source), f"/Fe:{output}"]
    else:
        compiler = args.compiler or os.getenv("CXX") or shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            raise SystemExit("No C++ compiler found (expected g++/clang++ or CXX).")
        cmd = [compiler, "-std=c++17", "-O3", "-shared"]
        if system != "windows":
            cmd.append("-fPIC")
        cmd += [str(source), "-o", str(output)]

    print("Building:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Built {output}")


if __name__ == "__main__":
    main()
