"""
Local Builder Module
====================

Handles local building of applications and tools.
Supports multiple build targets: Python executables, web apps, mobile apps, etc.


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    success: bool
    output_path: Optional[str] = None
    build_time: float = 0.0
    file_size: int = 0
    version: str = "1.0.0"
    build_type: str = "unknown"
    error_message: Optional[str] = None
    artifacts: List[str] = None  # type: ignore
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class LocalBuilder:
    
    def __init__(self, output_dir: str = "build_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.build_history = []
        
    def build_python_app(self, 
                        source_path: str, 
                        app_name: str,
                        entry_point: str = "main.py",
                        requirements: Optional[List[str]] = None,
                        version: str = "1.0.0") -> BuildResult:
        Build a Python application using PyInstaller
        
        Args:
            source_path: Path to the source code
            app_name: Name of the application
            entry_point: Main entry point file
            requirements: List of required packages
            version: Application version
            
        Returns:
            BuildResult with build information
        start_time = datetime.now()
        
        try:
            logger.info(f"Building Python app: {app_name}")
            
            # Ensure PyInstaller is installed
            self._ensure_pyinstaller()
            
            # Create build directory
            build_dir = self.output_dir / f"{app_name}_{version}"
            build_dir.mkdir(exist_ok=True)
            
            # Create requirements.txt if provided
            if requirements:
                req_file = Path(source_path) / "requirements.txt"
                with open(req_file, 'w') as f:
                    f.write('\n'.join(requirements))
            
            # Build with PyInstaller
            cmd = [
                "pyinstaller",
                "--onefile",
                "--name", app_name,
                "--distpath", str(build_dir),
                "--workpath", str(build_dir / "build"),
                "--specpath", str(build_dir),
                str(Path(source_path) / entry_point)
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=source_path)
            
            if result.returncode != 0:
                return BuildResult(
                    success=False,
                    error_message=f"Build failed: {result.stderr}",
                    build_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Find the built executable
            exe_path = build_dir / f"{app_name}.exe" if sys.platform == "win32" else build_dir / app_name
            
            if not exe_path.exists():
                return BuildResult(
                    success=False,
                    error_message="Executable not found after build",
                    build_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Get file size
            file_size = exe_path.stat().st_size
            
            # Record build
            build_result = BuildResult(
                success=True,
                output_path=str(exe_path),
                build_time=(datetime.now() - start_time).total_seconds(),
                file_size=file_size,
                version=version,
                build_type="python_executable",
                artifacts=[str(exe_path)]
            )
            
            self.build_history.append(build_result)
            self._save_build_info(build_result, build_dir)
            
            logger.info(f"✅ Build successful: {exe_path}")
            logger.info(f"📦 File size: {file_size / 1024 / 1024:.2f} MB")
            
            return build_result
            
        except Exception as e:
            logger.error(f"Build error: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=(datetime.now() - start_time).total_seconds()
            )
    
    def build_web_app(self, 
                     source_path: str, 
                     app_name: str,
                     framework: str = "flask",
                     version: str = "1.0.0") -> BuildResult:
        Build a web application
        
        Args:
            source_path: Path to the source code
            app_name: Name of the application
            framework: Web framework (flask, fastapi, django)
            version: Application version
            
        Returns:
            BuildResult with build information
        start_time = datetime.now()
        
        try:
            logger.info(f"Building web app: {app_name} ({framework})")
            
            # Create build directory
            build_dir = self.output_dir / f"{app_name}_{version}"
            build_dir.mkdir(exist_ok=True)
            
            # Copy source files
            source_path_obj = Path(source_path)
            for item in source_path_obj.rglob("*"):
                if item.is_file() and not any(part.startswith('.') for part in item.parts):
                    rel_path = item.relative_to(source_path_obj)
                    dest_path = build_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
            
            # Create startup script
            startup_script = self._create_web_startup_script(framework, app_name)
            startup_file = build_dir / "start.py"
            with open(startup_file, 'w') as f:
                f.write(startup_script)
            
            # Create requirements.txt
            requirements = self._get_web_requirements(framework)
            req_file = build_dir / "requirements.txt"
            with open(req_file, 'w') as f:
                f.write('\n'.join(requirements))
            
            # Create README
            readme_content = self._create_web_readme(app_name, framework, version)
            readme_file = build_dir / "README.md"
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            # Record build
            build_result = BuildResult(
                success=True,
                output_path=str(build_dir),
                build_time=(datetime.now() - start_time).total_seconds(),
                file_size=self._get_dir_size(build_dir),
                version=version,
                build_type=f"web_app_{framework}",
                artifacts=[str(build_dir)]
            )
            
            self.build_history.append(build_result)
            self._save_build_info(build_result, build_dir)
            
            logger.info(f"✅ Web app built: {build_dir}")
            
            return build_result
            
        except Exception as e:
            logger.error(f"Web app build error: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=(datetime.now() - start_time).total_seconds()
            )
    
    def build_cli_tool(self, 
                      source_path: str, 
                      tool_name: str,
                      entry_point: str = "main.py",
                      version: str = "1.0.0") -> BuildResult:
        Build a CLI tool
        
        Args:
            source_path: Path to the source code
            tool_name: Name of the tool
            entry_point: Main entry point file
            version: Tool version
            
        Returns:
            BuildResult with build information
        start_time = datetime.now()
        
        try:
            logger.info(f"Building CLI tool: {tool_name}")
            
            # Create build directory
            build_dir = self.output_dir / f"{tool_name}_{version}"
            build_dir.mkdir(exist_ok=True)
            
            # Copy source files
            source_path_obj = Path(source_path)
            for item in source_path_obj.rglob("*.py"):
                if not any(part.startswith('.') for part in item.parts):
                    rel_path = item.relative_to(source_path_obj)
                    dest_path = build_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
            
            # Create setup.py
            setup_content = self._create_setup_py(tool_name, version, entry_point)
            setup_file = build_dir / "setup.py"
            with open(setup_file, 'w') as f:
                f.write(setup_content)
            
            # Create requirements.txt
            requirements = self._get_cli_requirements()
            req_file = build_dir / "requirements.txt"
            with open(req_file, 'w') as f:
                f.write('\n'.join(requirements))
            
            # Create installation script
            install_script = self._create_install_script(tool_name)
            install_file = build_dir / "install.bat" if sys.platform == "win32" else build_dir / "install.sh"
            with open(install_file, 'w') as f:
                f.write(install_script)
            
            # Record build
            build_result = BuildResult(
                success=True,
                output_path=str(build_dir),
                build_time=(datetime.now() - start_time).total_seconds(),
                file_size=self._get_dir_size(build_dir),
                version=version,
                build_type="cli_tool",
                artifacts=[str(build_dir)]
            )
            
            self.build_history.append(build_result)
            self._save_build_info(build_result, build_dir)
            
            logger.info(f"✅ CLI tool built: {build_dir}")
            
            return build_result
            
        except Exception as e:
            logger.error(f"CLI tool build error: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _ensure_pyinstaller(self):
        try:
            import PyInstaller
        except ImportError:
            logger.info("Installing PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    def _create_web_startup_script(self, framework: str, app_name: str) -> str:
        if framework == "flask":
            return f'''#!/usr/bin/env python3
Startup script for {app_name}


# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your Flask app
try:
except ImportError:
    # Create a simple Flask app if app.py doesn't exist
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return f"<h1>Welcome to {app_name}</h1><p>Web app is running!</p>"

if __name__ == '__main__':
    print(f"Starting {app_name}...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
        elif framework == "fastapi":
            return f'''#!/usr/bin/env python3
Startup script for {app_name}

import os
import sys
import uvicorn

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your FastAPI app
try:
    from main import app
except ImportError:
    from fastapi import FastAPI
    app = FastAPI(title="{app_name}")
    
    @app.get("/")
    def read_root():
        return {{"message": f"Welcome to {app_name}"}}

if __name__ == '__main__':
    print(f"Starting {app_name}...")
    print("Open your browser and go to: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
        else:
            return f'''#!/usr/bin/env python3
Startup script for {app_name}

print(f"Starting {app_name}...")
print("Please configure your web framework manually.")
    
    def _get_web_requirements(self, framework: str) -> List[str]:
        base_requirements = ["gunicorn", "waitress"]
        
        if framework == "flask":
            return base_requirements + ["flask", "flask-cors"]
        elif framework == "fastapi":
            return base_requirements + ["fastapi", "uvicorn"]
        elif framework == "django":
            return base_requirements + ["django", "djangorestframework"]
        else:
            return base_requirements
    
    def _create_web_readme(self, app_name: str, framework: str, version: str) -> str:
        import textwrap
        body = (
            f"# {app_name}\n\n"
            f"A {framework} web application built with StillMe AI Framework.\n\n"
            "## Requirements\n"
            f"- Python {version}\n\n"
            "## Getting Started\n"
            "1) Install dependencies\n"
            "2) Run the server\n"
        )
        return textwrap.dedent(body)
    
    def _create_setup_py(self, tool_name: str, version: str, entry_point: str) -> str:
        return f'''from setuptools import setup, find_packages

setup(
    name="{tool_name}",
    version="{version}",
    description="A CLI tool built with StillMe AI Framework",
    author="StillMe AI Framework",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={{
        "console_scripts": [
            "{tool_name}={entry_point.replace('.py', '')}:main",
        ],
    }},
    python_requires=">=3.8",
)
    
    def _get_cli_requirements(self) -> List[str]:
        return [
            "click>=8.0.0",
            "rich>=13.0.0",
            "typer>=0.12.0",
        ]
    
    def _create_install_script(self, tool_name: str) -> str:
        if sys.platform == "win32":
            return f'''@echo off
echo Installing {tool_name}...
pip install -e .
echo Installation complete!
echo You can now run: {tool_name}
pause
        else:
            return f'''#!/bin/bash
echo "Installing {tool_name}..."
pip install -e .
echo "Installation complete!"
echo "You can now run: {tool_name}"
    
    def _get_dir_size(self, path: Path) -> int:
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def _save_build_info(self, result: BuildResult, build_dir: Path):
        info_file = build_dir / "build_info.json"
        info_data = {
            "success": result.success,
            "output_path": result.output_path,
            "build_time": result.build_time,
            "file_size": result.file_size,
            "version": result.version,
            "build_type": result.build_type,
            "error_message": result.error_message,
            "artifacts": result.artifacts,
            "build_timestamp": datetime.now().isoformat()
        }
        
        with open(info_file, 'w') as f:
            json.dump(info_data, f, indent=2)
    
    def get_build_history(self) -> List[BuildResult]:
        return self.build_history
    
    def get_build_summary(self) -> Dict[str, Any]:
        total_builds = len(self.build_history)
        successful_builds = sum(1 for b in self.build_history if b.success)
        
        return {
            "total_builds": total_builds,
            "successful_builds": successful_builds,
            "success_rate": successful_builds / total_builds if total_builds > 0 else 0,
            "latest_build": self.build_history[-1] if self.build_history else None
        }


import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import os
import sys
from flask import Flask
    from app import app

Local Builder Module
====================

Handles local building of applications and tools.
Supports multiple build targets: Python executables, web apps, mobile apps, etc.
"""


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """Result of a build operation"""
    success: bool
    output_path: Optional[str] = None
    build_time: float = 0.0
    file_size: int = 0
    version: str = "1.0.0"
    build_type: str = "unknown"
    error_message: Optional[str] = None
    artifacts: List[str] = None  # type: ignore
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class LocalBuilder:
    """Local application builder"""
    
    def __init__(self, output_dir: str = "build_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.build_history = []
        
    def build_python_app(self, 
                        source_path: str, 
                        app_name: str,
                        entry_point: str = "main.py",
                        requirements: Optional[List[str]] = None,
                        version: str = "1.0.0") -> BuildResult:
        """
        Build a Python application using PyInstaller
        
        Args:
            source_path: Path to the source code
            app_name: Name of the application
            entry_point: Main entry point file
            requirements: List of required packages
            version: Application version
            
        Returns:
            BuildResult with build information
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Building Python app: {app_name}")
            
            # Ensure PyInstaller is installed
            self._ensure_pyinstaller()
            
            # Create build directory
            build_dir = self.output_dir / f"{app_name}_{version}"
            build_dir.mkdir(exist_ok=True)
            
            # Create requirements.txt if provided
            if requirements:
                req_file = Path(source_path) / "requirements.txt"
                with open(req_file, 'w') as f:
                    f.write('\n'.join(requirements))
            
            # Build with PyInstaller
            cmd = [
                "pyinstaller",
                "--onefile",
                "--name", app_name,
                "--distpath", str(build_dir),
                "--workpath", str(build_dir / "build"),
                "--specpath", str(build_dir),
                str(Path(source_path) / entry_point)
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=source_path)
            
            if result.returncode != 0:
                return BuildResult(
                    success=False,
                    error_message=f"Build failed: {result.stderr}",
                    build_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Find the built executable
            exe_path = build_dir / f"{app_name}.exe" if sys.platform == "win32" else build_dir / app_name
            
            if not exe_path.exists():
                return BuildResult(
                    success=False,
                    error_message="Executable not found after build",
                    build_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Get file size
            file_size = exe_path.stat().st_size
            
            # Record build
            build_result = BuildResult(
                success=True,
                output_path=str(exe_path),
                build_time=(datetime.now() - start_time).total_seconds(),
                file_size=file_size,
                version=version,
                build_type="python_executable",
                artifacts=[str(exe_path)]
            )
            
            self.build_history.append(build_result)
            self._save_build_info(build_result, build_dir)
            
            logger.info(f"✅ Build successful: {exe_path}")
            logger.info(f"📦 File size: {file_size / 1024 / 1024:.2f} MB")
            
            return build_result
            
        except Exception as e:
            logger.error(f"Build error: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=(datetime.now() - start_time).total_seconds()
            )
    
    def build_web_app(self, 
                     source_path: str, 
                     app_name: str,
                     framework: str = "flask",
                     version: str = "1.0.0") -> BuildResult:
        """
        Build a web application
        
        Args:
            source_path: Path to the source code
            app_name: Name of the application
            framework: Web framework (flask, fastapi, django)
            version: Application version
            
        Returns:
            BuildResult with build information
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Building web app: {app_name} ({framework})")
            
            # Create build directory
            build_dir = self.output_dir / f"{app_name}_{version}"
            build_dir.mkdir(exist_ok=True)
            
            # Copy source files
            source_path_obj = Path(source_path)
            for item in source_path_obj.rglob("*"):
                if item.is_file() and not any(part.startswith('.') for part in item.parts):
                    rel_path = item.relative_to(source_path_obj)
                    dest_path = build_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
            
            # Create startup script
            startup_script = self._create_web_startup_script(framework, app_name)
            startup_file = build_dir / "start.py"
            with open(startup_file, 'w') as f:
                f.write(startup_script)
            
            # Create requirements.txt
            requirements = self._get_web_requirements(framework)
            req_file = build_dir / "requirements.txt"
            with open(req_file, 'w') as f:
                f.write('\n'.join(requirements))
            
            # Create README
            readme_content = self._create_web_readme(app_name, framework, version)
            readme_file = build_dir / "README.md"
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            # Record build
            build_result = BuildResult(
                success=True,
                output_path=str(build_dir),
                build_time=(datetime.now() - start_time).total_seconds(),
                file_size=self._get_dir_size(build_dir),
                version=version,
                build_type=f"web_app_{framework}",
                artifacts=[str(build_dir)]
            )
            
            self.build_history.append(build_result)
            self._save_build_info(build_result, build_dir)
            
            logger.info(f"✅ Web app built: {build_dir}")
            
            return build_result
            
        except Exception as e:
            logger.error(f"Web app build error: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=(datetime.now() - start_time).total_seconds()
            )
    
    def build_cli_tool(self, 
                      source_path: str, 
                      tool_name: str,
                      entry_point: str = "main.py",
                      version: str = "1.0.0") -> BuildResult:
        """
        Build a CLI tool
        
        Args:
            source_path: Path to the source code
            tool_name: Name of the tool
            entry_point: Main entry point file
            version: Tool version
            
        Returns:
            BuildResult with build information
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Building CLI tool: {tool_name}")
            
            # Create build directory
            build_dir = self.output_dir / f"{tool_name}_{version}"
            build_dir.mkdir(exist_ok=True)
            
            # Copy source files
            source_path_obj = Path(source_path)
            for item in source_path_obj.rglob("*.py"):
                if not any(part.startswith('.') for part in item.parts):
                    rel_path = item.relative_to(source_path_obj)
                    dest_path = build_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
            
            # Create setup.py
            setup_content = self._create_setup_py(tool_name, version, entry_point)
            setup_file = build_dir / "setup.py"
            with open(setup_file, 'w') as f:
                f.write(setup_content)
            
            # Create requirements.txt
            requirements = self._get_cli_requirements()
            req_file = build_dir / "requirements.txt"
            with open(req_file, 'w') as f:
                f.write('\n'.join(requirements))
            
            # Create installation script
            install_script = self._create_install_script(tool_name)
            install_file = build_dir / "install.bat" if sys.platform == "win32" else build_dir / "install.sh"
            with open(install_file, 'w') as f:
                f.write(install_script)
            
            # Record build
            build_result = BuildResult(
                success=True,
                output_path=str(build_dir),
                build_time=(datetime.now() - start_time).total_seconds(),
                file_size=self._get_dir_size(build_dir),
                version=version,
                build_type="cli_tool",
                artifacts=[str(build_dir)]
            )
            
            self.build_history.append(build_result)
            self._save_build_info(build_result, build_dir)
            
            logger.info(f"✅ CLI tool built: {build_dir}")
            
            return build_result
            
        except Exception as e:
            logger.error(f"CLI tool build error: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _ensure_pyinstaller(self):
        """Ensure PyInstaller is installed"""
        try:
            import pyinstaller
        except ImportError:
            logger.info("Installing PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    def _create_web_startup_script(self, framework: str, app_name: str) -> str:
        """Create startup script for web app"""
        if framework == "flask":
            return f'''#!/usr/bin/env python3
"""
Startup script for {app_name}
"""


# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your Flask app
try:
except ImportError:
    # Create a simple Flask app if app.py doesn't exist
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return f"<h1>Welcome to {app_name}</h1><p>Web app is running!</p>"

if __name__ == '__main__':
    print(f"Starting {app_name}...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
        elif framework == "fastapi":
            return f'''#!/usr/bin/env python3
"""
Startup script for {app_name}
"""


# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your FastAPI app
try:
except ImportError:
    app = FastAPI(title="{app_name}")
    
    @app.get("/")
    def read_root():
        return {{"message": f"Welcome to {app_name}"}}

if __name__ == '__main__':
    print(f"Starting {app_name}...")
    print("Open your browser and go to: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        else:
            return f'''#!/usr/bin/env python3
"""
Startup script for {app_name}
"""

print(f"Starting {app_name}...")
print("Please configure your web framework manually.")
'''
    
    def _get_web_requirements(self, framework: str) -> List[str]:
        """Get requirements for web framework"""
        base_requirements = ["gunicorn", "waitress"]
        
        if framework == "flask":
            return base_requirements + ["flask", "flask-cors"]
        elif framework == "fastapi":
            return base_requirements + ["fastapi", "uvicorn"]
        elif framework == "django":
            return base_requirements + ["django", "djangorestframework"]
        else:
            return base_requirements
    
    def _create_web_readme(self, app_name: str, framework: str, version: str) -> str:
        """Create README for web app"""
        return f"""# {app_name}

A {framework} web application built with StillMe AI Framework.

## Version: {version}

## Installation

1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running

```bash
python start.py
```

The application will be available at:
- Flask: http://localhost:5000
- FastAPI: http://localhost:8000
- Django: http://localhost:8000

## Features

- Built with StillMe AI Framework
- Local development ready
- Easy deployment

## Support

For support, contact StillMe AI Framework.
"""
    
    def _create_setup_py(self, tool_name: str, version: str, entry_point: str) -> str:
        """Create setup.py for CLI tool"""
        return f'''from setuptools import setup, find_packages

setup(
    name="{tool_name}",
    version="{version}",
    description="A CLI tool built with StillMe AI Framework",
    author="StillMe AI Framework",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={{
        "console_scripts": [
            "{tool_name}={entry_point.replace('.py', '')}:main",
        ],
    }},
    python_requires=">=3.8",
)
'''
    
    def _get_cli_requirements(self) -> List[str]:
        """Get requirements for CLI tool"""
        return [
            "click>=8.0.0",
            "rich>=13.0.0",
            "typer>=0.12.0",
        ]
    
    def _create_install_script(self, tool_name: str) -> str:
        """Create installation script"""
        if sys.platform == "win32":
            return f'''@echo off
echo Installing {tool_name}...
pip install -e .
echo Installation complete!
echo You can now run: {tool_name}
pause
'''
        else:
            return f'''#!/bin/bash
echo "Installing {tool_name}..."
pip install -e .
echo "Installation complete!"
echo "You can now run: {tool_name}"
f'''
    
    def _get_dir_size(self, path: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def _save_build_info(self, result: BuildResult, build_dir: Path):
        """Save build information to file"""
        info_file = build_dir / "build_info.json"
        info_data = {
            "success": result.success,
            "output_path": result.output_path,
            "build_time": result.build_time,
            "file_size": result.file_size,
            "version": result.version,
            "build_type": result.build_type,
            "error_message": result.error_message,
            "artifacts": result.artifacts,
            "build_timestamp": datetime.now().isoformat()
        }
        
        with open(info_file, 'w') as f:
            json.dump(info_data, f, indent=2)
    
    def get_build_history(self) -> List[BuildResult]:
        """Get build history"""
        return self.build_history
    
    def get_build_summary(self) -> Dict[str, Any]:
        """Get build summary"""
        total_builds = len(self.build_history)
        successful_builds = sum(1 for b in self.build_history if b.success)
        
        return {
            "total_builds": total_builds,
            "successful_builds": successful_builds,
            "success_rate": successful_builds / total_builds if total_builds > 0 else 0,
            "latest_build": self.build_history[-1] if self.build_history else None
        }
