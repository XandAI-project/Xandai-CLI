"""
XandAI LSP Integration

Language Server Protocol integration for enhanced code intelligence.
Provides automatic language server detection, code analysis, and AI-enhanced suggestions.
"""

from xandai.lsp.language_detector import LanguageDetector
from xandai.lsp.lsp_context_provider import LSPContextProvider
from xandai.lsp.lsp_manager import LSPManager

__all__ = ["LSPManager", "LSPContextProvider", "LanguageDetector"]
