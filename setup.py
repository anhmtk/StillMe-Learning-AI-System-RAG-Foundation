#!/usr/bin/env python3
"""
STILLME AI Framework - Setup Configuration
"""

from setuptools import setup, find_packages

setup(
    name="stillme-ai",
    version="2.1.0",
    description="STILLME AI Framework - Enterprise Edition",
    author="StillMe Framework Team",
    author_email="team@stillme.ai",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "cryptography>=45.0.0",
        "pytest>=8.4.0",
        "pytest-asyncio>=1.1.0",
        "httpx>=0.28.0",
        "openai>=1.0.0",
        "ollama>=0.5.0",
        "sentence-transformers>=5.1.0",
        "transformers>=4.56.0",
        "torch>=2.8.0",
        "numpy>=2.3.0",
        "PyYAML>=6.0.0",
        "psutil>=5.9.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.4.0",
            "pytest-asyncio>=1.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "ai": [
            "sentence-transformers>=5.1.0",
            "transformers>=4.56.0",
            "torch>=2.8.0",
            "ollama>=0.5.0",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Commercial",
        "Programming Language :: Python :: 3.12",
        "Topic :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
