#!/usr/bin/env python3
"""
XandAI - CLI Assistant with Ollama Integration
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="xandai-cli",
    version="2.1.5",
    author="XandAI-project",
    description="CLI Assistant with Ollama Integration and Context-Aware Interactions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/XandAI-project/Xandai-CLI",  # Add your repo URL
    project_urls={
        "Bug Tracker": "https://github.com/XandAI-project/XandAI-CLI/issues",
        "Documentation": "https://github.com/XandAI-project/XandAI-CLI#readme",
        "Source Code": "https://github.com/XandAI-project/XandAI-CLI",
        "Changelog": "https://github.com/XandAI-project/XandAI-CLI/releases",
    },
    keywords=["cli", "assistant", "ollama", "ai", "chatbot", "terminal", "automation"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Terminals",
        "Topic :: Utilities",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "xandai=xandai.main:main",
        ],
    },
    include_package_data=True,
)
