"""
LSP Context Provider Module

Provides LSP-enhanced context for AI chat interactions.
Enriches prompts with code intelligence information.
"""

from pathlib import Path
from typing import Dict, List, Optional

from xandai.lsp.lsp_manager import LSPManager


class LSPContextProvider:
    """
    LSP Context Provider

    Enriches AI prompts with Language Server Protocol intelligence.
    Provides code analysis, diagnostics, and project context.
    """

    def __init__(self, lsp_manager: LSPManager, verbose: bool = False):
        """
        Initialize LSP Context Provider

        Args:
            lsp_manager: LSP Manager instance
            verbose: Enable verbose logging
        """
        self.lsp_manager = lsp_manager
        self.verbose = verbose
        self._context_cache: Dict[str, Dict] = {}

    def get_project_context(self) -> str:
        """
        Get high-level project context for AI

        Returns:
            Formatted project context string
        """
        stats = self.lsp_manager.get_project_statistics()
        status = self.lsp_manager.get_lsp_status()

        context_parts = []

        # Project overview
        context_parts.append("PROJECT CONTEXT:")
        context_parts.append(f"- Type: {stats['project_type']}")
        context_parts.append(f"- Primary Language: {stats['primary_language']}")
        context_parts.append(f"- Total Source Files: {stats['total_files']}")

        # Language breakdown
        if stats["languages"]:
            context_parts.append("\nLANGUAGES:")
            for lang, info in stats["languages"].items():
                context_parts.append(
                    f"  - {lang.capitalize()}: {info['files']} files ({info['percentage']}%)"
                )

        # LSP servers status
        if status["active_servers"]:
            context_parts.append("\nACTIVE LSP SERVERS:")
            for lang, info in status["active_servers"].items():
                context_parts.append(f"  - {lang.capitalize()}: {info['server_name']}")

        # Available but not started
        if status["available_servers"]:
            context_parts.append("\nAVAILABLE LSP SERVERS (not started):")
            for lang, info in status["available_servers"].items():
                installed = "✓" if info["is_installed"] else "✗"
                context_parts.append(
                    f"  - {lang.capitalize()}: {info['server_name']} [{installed}]"
                )

        return "\n".join(context_parts)

    def get_file_context(self, file_path: str, include_diagnostics: bool = True) -> str:
        """
        Get LSP-enhanced context for a specific file

        Args:
            file_path: Path to the file
            include_diagnostics: Include diagnostic information

        Returns:
            Formatted file context string
        """
        # Check cache first
        cache_key = f"{file_path}:{include_diagnostics}"
        if cache_key in self._context_cache:
            cached = self._context_cache[cache_key]
            # Simple cache invalidation (could be more sophisticated)
            if self._is_cache_valid(cached):
                return cached["context"]

        context = self.lsp_manager.get_file_context(file_path)

        context_parts = []

        # File info
        context_parts.append(f"FILE: {Path(file_path).name}")
        context_parts.append(f"Language: {context['language']}")

        # LSP availability
        if context["lsp_available"]:
            context_parts.append(f"LSP: {context['server_info']['name']}")

            # Diagnostics
            if include_diagnostics and context["diagnostics"]:
                context_parts.append(f"\nDIAGNOSTICS ({len(context['diagnostics'])} issues):")
                for diag in context["diagnostics"][:5]:  # Limit to 5 most important
                    context_parts.append(f"  - {diag.get('message', 'Unknown issue')}")

                if len(context["diagnostics"]) > 5:
                    context_parts.append(f"  ... and {len(context['diagnostics']) - 5} more")
        else:
            context_parts.append("LSP: Not available")

        result = "\n".join(context_parts)

        # Cache result
        self._context_cache[cache_key] = {"context": result, "timestamp": self._get_timestamp()}

        return result

    def get_code_intelligence_prompt(
        self, user_query: str, relevant_files: List[str] = None
    ) -> str:
        """
        Generate an enhanced system prompt with LSP intelligence

        Args:
            user_query: User's query/request
            relevant_files: List of relevant file paths

        Returns:
            Enhanced prompt with code intelligence
        """
        prompt_parts = []

        # Add project context
        prompt_parts.append(self.get_project_context())

        # Add file-specific context if files mentioned
        if relevant_files:
            prompt_parts.append("\n\nRELEVANT FILES:")
            for file_path in relevant_files[:3]:  # Limit to avoid token explosion
                try:
                    file_context = self.get_file_context(file_path)
                    prompt_parts.append(f"\n{file_context}")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Could not get context for {file_path}: {e}")

        # Add LSP capabilities note
        if self.lsp_manager.get_active_languages():
            prompt_parts.append("\n\nCODE INTELLIGENCE AVAILABLE:")
            prompt_parts.append("LSP servers are active. Use them for:")
            prompt_parts.append("- Accurate syntax validation")
            prompt_parts.append("- Type-aware suggestions")
            prompt_parts.append("- Project-specific conventions")
            prompt_parts.append("- Real-time error detection")

        return "\n".join(prompt_parts)

    def extract_file_references(self, text: str) -> List[str]:
        """
        Extract file references from text

        Args:
            text: Text to analyze

        Returns:
            List of file paths found in text
        """
        import re

        files = []

        # Common file patterns
        patterns = [
            r"(?:^|\s)([a-zA-Z0-9_\-./\\]+\.(?:py|js|ts|java|cpp|c|rs|go|rb|php|html|css|json))",
            r"`([a-zA-Z0-9_\-./\\]+\.(?:py|js|ts|java|cpp|c|rs|go|rb|php|html|css|json))`",
            r'"([a-zA-Z0-9_\-./\\]+\.(?:py|js|ts|java|cpp|c|rs|go|rb|php|html|css|json))"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            files.extend(matches)

        # Validate files exist
        valid_files = []
        root = Path(self.lsp_manager.root_path)

        for file_path in files:
            abs_path = root / file_path
            if abs_path.exists() and abs_path.is_file():
                valid_files.append(str(abs_path))

        return valid_files

    def get_diagnostics_summary(self) -> Dict:
        """
        Get summary of diagnostics across all active LSP servers

        Returns:
            Dictionary with diagnostics summary
        """
        summary = {
            "total_issues": 0,
            "by_language": {},
            "by_severity": {"error": 0, "warning": 0, "info": 0},
        }

        # This would require tracking diagnostics from LSP notifications
        # For now, return basic structure

        return summary

    def suggest_lsp_servers(self) -> List[Dict]:
        """
        Suggest LSP servers that should be installed

        Returns:
            List of server suggestions
        """
        status = self.lsp_manager.get_lsp_status()
        suggestions = []

        for lang, info in status["available_servers"].items():
            if not info["is_installed"]:
                suggestions.append(
                    {
                        "language": lang,
                        "server": info["server_name"],
                        "install_command": info["install_command"],
                        "file_count": info["file_count"],
                        "priority": "high" if info["file_count"] > 10 else "medium",
                    }
                )

        # Sort by priority and file count
        suggestions.sort(key=lambda x: (x["priority"], x["file_count"]), reverse=True)

        return suggestions

    def format_lsp_status_for_user(self) -> str:
        """
        Format LSP status in a user-friendly way

        Returns:
            Formatted status string
        """
        status = self.lsp_manager.get_lsp_status()

        lines = []
        lines.append("📊 LSP STATUS")
        lines.append("=" * 50)

        # Active servers
        if status["active_servers"]:
            lines.append("\n✅ Active LSP Servers:")
            for lang, info in status["active_servers"].items():
                lines.append(
                    f"  • {lang.capitalize()}: {info['server_name']} ({info['file_count']} files)"
                )
        else:
            lines.append("\n⚠️  No active LSP servers")

        # Suggestions
        suggestions = self.suggest_lsp_servers()
        if suggestions:
            lines.append("\n💡 Recommended LSP Servers:")
            for sug in suggestions[:3]:  # Show top 3
                lines.append(f"  • {sug['language'].capitalize()}: {sug['server']}")
                lines.append(f"    Install: {sug['install_command']}")

        # Project stats
        stats = status["project_stats"]
        lines.append(f"\n📁 Project: {stats['project_type']}")
        lines.append(f"   Primary Language: {stats['primary_language']}")
        lines.append(f"   Total Files: {stats['total_files']}")

        return "\n".join(lines)

    def clear_cache(self):
        """Clear context cache"""
        self._context_cache.clear()

    def _is_cache_valid(self, cached_entry: Dict, max_age_seconds: int = 60) -> bool:
        """Check if cached entry is still valid"""
        import time

        if "timestamp" not in cached_entry:
            return False

        age = time.time() - cached_entry["timestamp"]
        return age < max_age_seconds

    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time

        return time.time()
