"""
Test LSP Integration

Tests for Language Server Protocol integration in XandAI-CLI
"""

import os
from pathlib import Path

import pytest

from xandai.lsp.language_detector import LanguageDetector
from xandai.lsp.lsp_config import (
    get_available_servers,
    get_server_for_file,
    get_server_for_language,
)


class TestLanguageDetector:
    """Test language detection functionality"""

    def test_extension_mapping(self):
        """Test file extension to language mapping"""
        detector = LanguageDetector()

        assert detector.get_file_language("test.py") == "python"
        assert detector.get_file_language("test.js") == "javascript"
        assert detector.get_file_language("test.ts") == "typescript"
        assert detector.get_file_language("test.rs") == "rust"
        assert detector.get_file_language("test.go") == "go"
        assert detector.get_file_language("test.unknown") == "unknown"

    def test_detect_languages_in_current_project(self):
        """Test language detection in current project"""
        detector = LanguageDetector(max_depth=3)
        languages = detector.detect_languages(min_files=1)

        # Should detect Python in this project
        assert "python" in languages
        assert languages["python"] > 0

    def test_get_primary_language(self):
        """Test primary language detection"""
        detector = LanguageDetector(max_depth=3)
        primary = detector.get_primary_language()

        # This project is primarily Python
        assert primary == "python"

    def test_get_statistics(self):
        """Test project statistics"""
        detector = LanguageDetector(max_depth=3)
        stats = detector.get_statistics()

        assert "total_files" in stats
        assert "language_count" in stats
        assert "primary_language" in stats
        assert "project_type" in stats
        assert "languages" in stats

        assert stats["total_files"] > 0
        assert stats["primary_language"] == "python"


class TestLSPConfig:
    """Test LSP configuration"""

    def test_get_server_for_language(self):
        """Test getting server config for language"""
        python_server = get_server_for_language("python")

        assert python_server is not None
        assert python_server.language == "python"
        assert python_server.name in ["Pyright", "Jedi Language Server"]
        assert len(python_server.file_extensions) > 0
        assert ".py" in python_server.file_extensions

    def test_get_server_for_file(self):
        """Test getting server config for file"""
        python_server = get_server_for_file("test.py")
        js_server = get_server_for_file("test.js")

        assert python_server is not None
        assert python_server.language == "python"

        assert js_server is not None
        assert js_server.language == "javascript"

    def test_get_server_for_unknown_file(self):
        """Test getting server for unknown file type"""
        server = get_server_for_file("test.unknown")
        assert server is None

    def test_server_installation_check(self):
        """Test server installation detection"""
        python_server = get_server_for_language("python")

        # is_installed() should return bool
        installed = python_server.is_installed()
        assert isinstance(installed, bool)


class TestLSPTool:
    """Test LSP tool functionality"""

    def test_lsp_tool_import(self):
        """Test that LSP tool can be imported"""
        from tools.lsp_tool import LSPTool

        tool = LSPTool()
        assert tool.get_name() == "lsp_tool"
        assert "code intelligence" in tool.get_description().lower()

    def test_lsp_tool_parameters(self):
        """Test LSP tool parameters"""
        from tools.lsp_tool import LSPTool

        tool = LSPTool()
        params = tool.get_parameters()

        assert "operation" in params
        assert "file_path" in params

    def test_lsp_tool_status_operation(self):
        """Test LSP tool status operation"""
        from tools.lsp_tool import LSPTool

        tool = LSPTool()
        result = tool.execute(operation="status")

        assert "success" in result
        assert "operation" in result

        if result["success"]:
            assert result["operation"] == "status"
            assert "lsp_initialized" in result

    def test_lsp_tool_project_info_operation(self):
        """Test LSP tool project info operation"""
        from tools.lsp_tool import LSPTool

        tool = LSPTool()
        result = tool.execute(operation="project_info")

        assert "success" in result

        if result["success"]:
            assert "project_type" in result
            assert "primary_language" in result
            assert "total_files" in result
            assert result["primary_language"] == "python"


class TestLSPContextProvider:
    """Test LSP context provider"""

    def test_context_provider_import(self):
        """Test that context provider can be imported"""
        from xandai.lsp import LSPContextProvider, LSPManager

        manager = LSPManager(verbose=False)
        provider = LSPContextProvider(manager, verbose=False)

        assert provider is not None
        assert provider.lsp_manager is manager

    def test_get_project_context(self):
        """Test getting project context"""
        from xandai.lsp import LSPContextProvider, LSPManager

        manager = LSPManager(verbose=False)
        provider = LSPContextProvider(manager, verbose=False)

        context = provider.get_project_context()

        assert isinstance(context, str)
        assert len(context) > 0
        assert "PROJECT CONTEXT" in context

    def test_extract_file_references(self):
        """Test extracting file references from text"""
        from xandai.lsp import LSPContextProvider, LSPManager

        manager = LSPManager(verbose=False)
        provider = LSPContextProvider(manager, verbose=False)

        text = "Check main.py and utils.js for errors"
        files = provider.extract_file_references(text)

        # Should extract file references (if they exist)
        assert isinstance(files, list)


class TestChatProcessorIntegration:
    """Test ChatProcessor LSP integration"""

    def test_chat_processor_with_lsp(self):
        """Test that ChatProcessor accepts LSP context provider"""
        from xandai.conversation.conversation_manager import ConversationManager
        from xandai.lsp import LSPContextProvider, LSPManager
        from xandai.processors.chat_processor import ChatProcessor

        # Mock LLM provider
        class MockLLMProvider:
            def chat(self, messages, temperature=0.7, max_tokens=2048):
                class MockResponse:
                    content = "Test response"
                    model = "test-model"
                    total_tokens = 100

                return MockResponse()

        llm_provider = MockLLMProvider()
        conv_manager = ConversationManager()

        # Create LSP components
        lsp_manager = LSPManager(verbose=False)
        lsp_context = LSPContextProvider(lsp_manager, verbose=False)

        # Create chat processor with LSP
        processor = ChatProcessor(
            llm_provider=llm_provider,
            conversation_manager=conv_manager,
            lsp_context_provider=lsp_context,
        )

        assert processor.lsp_context_provider is not None
        assert processor.lsp_context_provider is lsp_context

    def test_chat_processor_without_lsp(self):
        """Test that ChatProcessor works without LSP"""
        from xandai.conversation.conversation_manager import ConversationManager
        from xandai.processors.chat_processor import ChatProcessor

        # Mock LLM provider
        class MockLLMProvider:
            def chat(self, messages, temperature=0.7, max_tokens=2048):
                class MockResponse:
                    content = "Test response"
                    model = "test-model"
                    total_tokens = 100

                return MockResponse()

        llm_provider = MockLLMProvider()
        conv_manager = ConversationManager()

        # Create chat processor without LSP
        processor = ChatProcessor(
            llm_provider=llm_provider, conversation_manager=conv_manager, lsp_context_provider=None
        )

        assert processor.lsp_context_provider is None


def test_lsp_module_imports():
    """Test that all LSP modules can be imported"""
    from xandai.lsp import LanguageDetector, LSPContextProvider, LSPManager
    from xandai.lsp.lsp_client import LSPClient
    from xandai.lsp.lsp_config import LSPServerConfig, get_server_for_language

    assert LSPManager is not None
    assert LSPContextProvider is not None
    assert LanguageDetector is not None
    assert LSPServerConfig is not None
    assert LSPClient is not None


def test_lsp_is_optional():
    """Test that LSP is truly optional and doesn't break existing functionality"""
    # This test verifies that importing core modules doesn't require LSP
    from xandai.conversation.conversation_manager import ConversationManager
    from xandai.core.app_state import AppState

    app_state = AppState()
    conv_manager = ConversationManager()

    # Should work without LSP
    assert app_state is not None
    assert conv_manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
