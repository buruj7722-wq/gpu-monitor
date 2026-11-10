"""Copy the existing editable web assets into wheels without duplicate sources."""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithDashboard(build_py):
    def run(self) -> None:
        super().run()
        destination = Path(self.build_lib) / "monitor/web"
        for directory in ["templates", "static"]:
            shutil.copytree(directory, destination / directory, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildWithDashboard})
