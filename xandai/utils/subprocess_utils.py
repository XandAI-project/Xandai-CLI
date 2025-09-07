"""
Subprocess Utilities

Funções utilitárias para executar subprocessos de forma segura
com tratamento adequado de encoding, especialmente no Windows.
"""

import os
import subprocess
from typing import Any, Dict, List, Optional, Union


def safe_subprocess_run(*args, **kwargs) -> subprocess.CompletedProcess:
    """
    Wrapper seguro para subprocess.run com encoding adequado

    Automatically handles encoding issues that can occur on Windows
    and other systems with non-UTF-8 default encodings.

    Args:
        *args: Arguments to pass to subprocess.run
        **kwargs: Keyword arguments to pass to subprocess.run

    Returns:
        CompletedProcess result
    """
    # Set safe default encoding parameters if text=True is specified
    if kwargs.get("text", False) or kwargs.get("universal_newlines", False):
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"
        if "errors" not in kwargs:
            kwargs["errors"] = "replace"  # Replace invalid characters instead of crashing

    return subprocess.run(*args, **kwargs)


def safe_subprocess_popen(*args, **kwargs) -> subprocess.Popen:
    """
    Wrapper seguro para subprocess.Popen com encoding adequado

    Args:
        *args: Arguments to pass to subprocess.Popen
        **kwargs: Keyword arguments to pass to subprocess.Popen

    Returns:
        Popen object
    """
    # Set safe default encoding parameters if text=True is specified
    if kwargs.get("text", False) or kwargs.get("universal_newlines", False):
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"
        if "errors" not in kwargs:
            kwargs["errors"] = "replace"  # Replace invalid characters instead of crashing

    return subprocess.Popen(*args, **kwargs)


def execute_command_safe(
    command: Union[str, List[str]],
    timeout: Optional[int] = 30,
    capture_output: bool = True,
    cwd: Optional[str] = None,
    shell: bool = True,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    Execute a command safely with proper encoding handling

    Args:
        command: Command to execute
        timeout: Timeout in seconds
        capture_output: Whether to capture output
        cwd: Working directory
        shell: Whether to use shell
        **kwargs: Additional arguments

    Returns:
        CompletedProcess result
    """
    return safe_subprocess_run(
        command,
        shell=shell,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        cwd=cwd,
        **kwargs,
    )


def get_safe_env() -> Dict[str, str]:
    """
    Get environment variables with safe encoding settings

    Returns:
        Environment dictionary with UTF-8 settings
    """
    env = os.environ.copy()

    # Ensure UTF-8 encoding for Python subprocesses
    env["PYTHONIOENCODING"] = "utf-8"

    # Set locale to UTF-8 if possible
    if os.name == "nt":  # Windows
        env["CHCP"] = "65001"  # UTF-8 code page
    else:  # Unix-like
        env["LC_ALL"] = env.get("LC_ALL", "C.UTF-8")
        env["LANG"] = env.get("LANG", "C.UTF-8")

    return env
