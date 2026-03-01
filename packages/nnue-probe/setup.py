from __future__ import annotations

import re
import subprocess
from pathlib import Path

from setuptools import Command, setup
from setuptools.command.build_py import build_py


ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "nnue_probe"
HEADER_FILE = ROOT / "src" / "nnue.h"


def _default_network_name() -> str:
    text = HEADER_FILE.read_text(encoding="utf-8")
    match = re.search(r'#define\s+DefaultEvalFile\s+"([^"]+)"', text)
    if not match:
        raise RuntimeError(f"Could not parse DefaultEvalFile from {HEADER_FILE}")
    return match.group(1)


class BuildNative(Command):
    description = "Build nnueprobe shared library and NNUE network in-package"
    user_options: list[tuple[str, str | None, str]] = []

    def initialize_options(self) -> None:
        return None

    def finalize_options(self) -> None:
        return None

    def run(self) -> None:
        PACKAGE_DIR.mkdir(exist_ok=True)

        # Make the nnueprobe shared library
        subprocess.check_call(["make"], cwd=ROOT)

        # Ensure library exists
        built_lib = PACKAGE_DIR / "libnnueprobe.so"
        if not built_lib.exists():
            raise RuntimeError(f"Expected native library at {built_lib}")

        # Ensure NNUE exists
        network_file = PACKAGE_DIR / _default_network_name()
        if not network_file.exists():
            raise RuntimeError(f"Expected NNUE network file at {network_file}")


class BuildPyWithNative(build_py):
    def run(self) -> None:
        self.run_command("build_native")
        super().run()


setup(
    name="nnue-probe",
    version="0.1.0",
    description="NNUE probe library with Python ctypes wrapper",
    packages=["nnue_probe"],
    include_package_data=True,
    package_data={"nnue_probe": ["libnnueprobe.so", "nn-*.nnue"]},
    cmdclass={
        "build_native": BuildNative,
        "build_py": BuildPyWithNative,
    },
)
