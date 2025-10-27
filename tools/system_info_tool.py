"""
System Info Tool - Get system and environment information
"""

import os
import platform
import sys
from datetime import datetime


class SystemInfoTool:
    """Get system and environment information."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "system_info_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return (
            "Get system information including OS, Python version, environment variables, and more"
        )

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "info_type": "string (optional) - Type of info: 'all', 'os', 'python', 'env', 'paths' (default: 'all')",
        }

    def execute(self, info_type: str = "all"):
        """
        Execute the system info retrieval.

        Args:
            info_type: Type of information to retrieve

        Returns:
            Dictionary with system information
        """
        try:
            info_type = info_type.lower()
            result = {"success": True, "timestamp": datetime.now().isoformat()}

            # OS Information
            if info_type in ["all", "os"]:
                result["os"] = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "architecture": platform.architecture()[0],
                    "hostname": platform.node(),
                }

            # Python Information
            if info_type in ["all", "python"]:
                result["python"] = {
                    "version": sys.version.split()[0],
                    "full_version": sys.version,
                    "implementation": platform.python_implementation(),
                    "compiler": platform.python_compiler(),
                    "executable": sys.executable,
                    "prefix": sys.prefix,
                }

            # Environment Variables (limited list for security)
            if info_type in ["all", "env"]:
                safe_env_vars = [
                    "PATH",
                    "HOME",
                    "USER",
                    "SHELL",
                    "LANG",
                    "PWD",
                    "TERM",
                    "EDITOR",
                    "PYTHONPATH",
                    "VIRTUAL_ENV",
                ]
                result["environment"] = {
                    key: os.environ.get(key, "Not set")
                    for key in safe_env_vars
                    if key in os.environ
                }
                result["environment"]["env_var_count"] = len(os.environ)

            # Path Information
            if info_type in ["all", "paths"]:
                result["paths"] = {
                    "current_directory": os.getcwd(),
                    "home_directory": os.path.expanduser("~"),
                    "temp_directory": os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp",
                    "python_path": sys.path[:5],  # First 5 paths
                }

            # Resource Information (if available)
            if info_type in ["all"]:
                try:
                    import psutil

                    result["resources"] = {
                        "cpu_count": psutil.cpu_count(),
                        "cpu_percent": f"{psutil.cpu_percent(interval=0.1)}%",
                        "memory": {
                            "total": self._format_bytes(psutil.virtual_memory().total),
                            "available": self._format_bytes(psutil.virtual_memory().available),
                            "percent_used": f"{psutil.virtual_memory().percent}%",
                        },
                        "disk": {
                            "total": self._format_bytes(psutil.disk_usage("/").total),
                            "free": self._format_bytes(psutil.disk_usage("/").free),
                            "percent_used": f"{psutil.disk_usage('/').percent}%",
                        },
                    }
                except ImportError:
                    result["resources"] = {
                        "note": "Install 'psutil' package for detailed resource information"
                    }

            if info_type not in ["all", "os", "python", "env", "paths"]:
                return {
                    "success": False,
                    "error": f"Unknown info_type: {info_type}. Use: all, os, python, env, paths",
                }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"System info error: {str(e)}",
            }

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
