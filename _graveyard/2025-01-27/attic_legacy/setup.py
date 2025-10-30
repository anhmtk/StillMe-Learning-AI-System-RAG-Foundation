#!/usr/bin/env python3
"""
StillMe AI Framework Setup
Thiết lập StillMe AI Framework
"""

from setuptools import find_packages, setup

setup(
    name="stillme-ai",
    version="2.1.1",
    description="StillMe AI Framework - Advanced AI Platform",
    long_description="StillMe AI Framework with Common Layer architecture",
    author="StillMe AI Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "httpx>=0.24.0",
        "aiofiles>=0.7.0",
        "pyyaml>=6.0",
        "pytest>=6.0.0",
        "pytest-asyncio>=0.15.0",
        "pytest-cov>=2.12.0",
    ],
    extras_require={
        "dev": [
            "ruff>=0.1.0",
            "pyright>=1.1.0",
            "radon>=5.1.0",
            "vulture>=2.0.0",
        ]
    },
)
