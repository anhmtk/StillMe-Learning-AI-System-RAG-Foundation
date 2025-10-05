"""Local Packager Module
=======================

Handles packaging and distribution of applications.
Creates installable packages, archives, and distribution files.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tarfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import textwrap

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PackageResult:
    """Result of a packaging operation."""
    success: bool
    package_path: Optional[str] = None
    package_type: str = "unknown"
    file_size: int = 0
    version: str = "1.0.0"
    error_message: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)

class LocalPackager:
    """Local application packager."""

    def __init__(self, output_dir: str = "packages") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.package_history: List[PackageResult] = []

    # ----------------------- public APIs -----------------------

    def create_zip_package(
        self,
        source_path: str,
        package_name: str,
        version: str = "1.0.0",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> PackageResult:
        """Create a ZIP package."""
        try:
            logger.info("Creating ZIP package: %s", package_name)
            package_path = self.output_dir / f"{package_name}_{version}.zip"
            with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                root = Path(source_path)
                for item in root.rglob("*"):
                    if item.is_file() and self._should_include_file(item, include_patterns, exclude_patterns):
                        zipf.write(item, item.relative_to(root))
            result = PackageResult(
                success=True,
                package_path=str(package_path),
                package_type="zip",
                file_size=package_path.stat().st_size,
                version=version,
                artifacts=[str(package_path)],
            )
            self.package_history.append(result)
            self._save_package_info(result)
            return result
        except Exception as e:  # pragma: no cover (để tránh đòi hỏi I/O lỗi trong unit)
            logger.error("ZIP packaging error: %s", e)
            return PackageResult(success=False, error_message=str(e), package_type="zip")

    def create_tar_package(
        self,
        source_path: str,
        package_name: str,
        version: str = "1.0.0",
        compression: str = "gz",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> PackageResult:
        """Create a TAR package."""
        try:
            logger.info("Creating TAR package: %s", package_name)
            mode = {"gz": "w:gz", "bz2": "w:bz2", "xz": "w:xz"}.get(compression, "w")
            suffix = {"gz": ".tar.gz", "bz2": ".tar.bz2", "xz": ".tar.xz"}.get(compression, ".tar")
            package_path = self.output_dir / f"{package_name}_{version}{suffix}"
            with tarfile.open(package_path, mode) as tarf:
                root = Path(source_path)
                for item in root.rglob("*"):
                    if item.is_file() and self._should_include_file(item, include_patterns, exclude_patterns):
                        tarf.add(item, arcname=item.relative_to(root))
            result = PackageResult(
                success=True,
                package_path=str(package_path),
                package_type=f"tar_{compression if compression in {'gz','bz2','xz'} else 'plain'}",
                file_size=package_path.stat().st_size,
                version=version,
                artifacts=[str(package_path)],
            )
            self.package_history.append(result)
            self._save_package_info(result)
            return result
        except Exception as e:  # pragma: no cover
            logger.error("TAR packaging error: %s", e)
            return PackageResult(success=False, error_message=str(e), package_type=f"tar_{compression}")

    def create_installer_package(
        self,
        source_path: str,
        package_name: str,
        version: str = "1.0.0",
        installer_type: str = "nsis",
    ) -> PackageResult:
        """Create an 'installer' folder with script + README."""
        try:
            logger.info("Creating installer package: %s", package_name)
            package_dir = self.output_dir / f"{package_name}_{version}_installer"
            package_dir.mkdir(parents=True, exist_ok=True)

            # copy sources (light; skip dot folders)
            root = Path(source_path)
            for item in root.rglob("*"):
                if item.is_file() and not any(part.startswith(".") for part in item.parts):
                    dst = package_dir / item.relative_to(root)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dst)

            if installer_type == "nsis":
                script = self._create_nsis_script(package_name, version)
                script_file = package_dir / "installer.nsi"
            elif installer_type == "inno":
                script = self._create_inno_script(package_name, version)
                script_file = package_dir / "installer.iss"
            else:
                script = self._create_batch_installer(package_name, version)
                script_file = package_dir / "install.bat"

            script_file.write_text(script, encoding="utf-8")

            readme = self._create_installer_readme(package_name, version, installer_type)
            (package_dir / "README.md").write_text(readme, encoding="utf-8")

            size = self._get_dir_size(package_dir)
            result = PackageResult(
                success=True,
                package_path=str(package_dir),
                package_type=f"installer_{installer_type}",
                file_size=size,
                version=version,
                artifacts=[str(package_dir)],
            )
            self.package_history.append(result)
            self._save_package_info(result)
            return result
        except Exception as e:  # pragma: no cover
            logger.error("Installer packaging error: %s", e)
            return PackageResult(success=False, error_message=str(e), package_type=f"installer_{installer_type}")

    def create_docker_package(
        self,
        source_path: str,
        package_name: str,
        version: str = "1.0.0",
        base_image: str = "python:3.12-slim",
    ) -> PackageResult:
        """Create a Docker packaging folder (Dockerfile, compose, README)."""
        try:
            logger.info("Creating Docker package: %s", package_name)
            package_dir = self.output_dir / f"{package_name}_{version}_docker"
            package_dir.mkdir(parents=True, exist_ok=True)

            root = Path(source_path)
            for item in root.rglob("*"):
                if item.is_file() and not any(part.startswith(".") for part in item.parts):
                    dst = package_dir / item.relative_to(root)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dst)

            (package_dir / "Dockerfile").write_text(self._create_dockerfile(package_name, base_image), encoding="utf-8")
            (package_dir / "docker-compose.yml").write_text(self._create_docker_compose(package_name, version), encoding="utf-8")
            (package_dir / ".dockerignore").write_text(self._create_dockerignore(), encoding="utf-8")
            (package_dir / "README.md").write_text(self._create_docker_readme(package_name, version), encoding="utf-8")

            size = self._get_dir_size(package_dir)
            result = PackageResult(
                success=True,
                package_path=str(package_dir),
                package_type="docker",
                file_size=size,
                version=version,
                artifacts=[str(package_dir)],
            )
            self.package_history.append(result)
            self._save_package_info(result)
            return result
        except Exception as e:  # pragma: no cover
            logger.error("Docker packaging error: %s", e)
            return PackageResult(success=False, error_message=str(e), package_type="docker")

    # ----------------------- helpers -----------------------

    def _should_include_file(
        self,
        file_path: Path,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
    ) -> bool:
        p = str(file_path)
        if exclude_patterns and any((pat in p) or file_path.match(pat) for pat in exclude_patterns):
            return False
        if include_patterns:
            return any((pat in p) or file_path.match(pat) for pat in include_patterns)
        for pat in ["__pycache__", ".git", ".pytest_cache", "*.pyc", "*.pyo", ".env", "venv", "env", ".venv"]:
            if (pat in p) or file_path.match(pat):
                return False
        return True

    # --- script templates (note: braces for NSIS/Inno must be doubled) ---

    def _create_nsis_script(self, package_name: str, version: str) -> str:
        return textwrap.dedent(
            f"""\
            !define APPNAME "{package_name}"
            !define COMPANYNAME "StillMe AI Framework"
            !define DESCRIPTION "A {package_name} application"
            !define VERSIONMAJOR 1
            !define VERSIONMINOR 0
            !define VERSIONBUILD 0

            RequestExecutionLevel admin
            InstallDir "$PROGRAMFILES\\${{APPNAME}}"
            Name "${{COMPANYNAME}} - ${{APPNAME}}"
            outFile "${{APPNAME}}_installer.exe"

            page directory
            page instfiles

            section "install"
                setOutPath $INSTDIR
                file /r "."
                writeUninstaller "$INSTDIR\\uninstall.exe"
            sectionEnd

            section "uninstall"
                delete "$INSTDIR\\uninstall.exe"
                rmDir /r "$INSTDIR"
            sectionEnd
            """
        )

    def _create_inno_script(self, package_name: str, version: str) -> str:
        return textwrap.dedent(
            f"""\
            [Setup]
            AppName={package_name}
            AppVersion={version}
            DefaultDirName={{{{autopf}}}}\\{package_name}
            OutputBaseFilename={package_name}_installer

            [Files]
            Source: "*"; DestDir: "{{{{app}}}}"; Flags: ignoreversion recursesubdirs createallsubdirs

            [Icons]
            Name: "{{{{group}}}}\\{package_name}"; Filename: "{{{{app}}}}\\start.py"
            """
        )

    def _create_batch_installer(self, package_name: str, version: str) -> str:
        return textwrap.dedent(
            f"""\
            @echo off
            echo Installing {package_name} v{version}...
            echo Python found. Installing dependencies...
            pip install -r requirements.txt
            echo Installation complete!
            """
        )

    def _create_installer_readme(self, package_name: str, version: str, installer_type: str) -> str:
        return textwrap.dedent(
            f"""\
            # {package_name} Installer

            Version: {version}
            Installer Type: {installer_type}

            ## Installation
            - Run the installer script for your platform.
            - Follow on-screen instructions.

            ## Requirements
            - Python 3.8+ (for batch installer)
            """
        )

    def _create_dockerfile(self, package_name: str, base_image: str) -> str:
        return textwrap.dedent(
            f"""\
            FROM {base_image}
            WORKDIR /app
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt
            COPY . .
            EXPOSE 8000
            CMD ["python", "start.py"]
            """
        )

    def _create_docker_compose(self, package_name: str, version: str) -> str:
        return textwrap.dedent(
            f"""\
            version: '3.8'
            services:
              {package_name}:
                build: .
                container_name: {package_name}_{version}
                ports:
                  - "8000:8000"
                environment:
                  - PYTHONUNBUFFERED=1
            """
        )

    def _create_dockerignore(self) -> str:
        return textwrap.dedent(
            """\
            __pycache__/
            *.py[cod]
            .venv/
            .env
            .git
            *.log
            htmlcov/
            """
        )

    # --- persistence ---

    def _get_dir_size(self, path: Path) -> int:
        total = 0
        for fp in path.rglob("*"):
            if fp.is_file():
                total += fp.stat().st_size
        return total

    def _save_package_info(self, result: PackageResult) -> None:
        info_file = self.output_dir / "package_info.json"
        data: Dict[str, Any]
        if info_file.exists():
            data = json.loads(info_file.read_text(encoding="utf-8"))
        else:
            data = {"packages": []}
        data["packages"].append(
            {
                "success": result.success,
                "package_path": result.package_path,
                "package_type": result.package_type,
                "file_size": result.file_size,
                "version": result.version,
                "error_message": result.error_message,
                "artifacts": result.artifacts,
                "timestamp": datetime.now().isoformat(),
            }
        )
        info_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
