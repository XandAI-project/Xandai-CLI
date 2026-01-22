"""
Tests for UI Components
"""

from io import StringIO

import pytest
from rich.console import Console

from xandai.ui.components import CodeBlock, MessageBox, Panel, StatusIndicator, Table
from xandai.ui.streaming import StreamingOutput, StreamManager
from xandai.ui.theme import Theme, ThemeManager


class TestUIComponents:
    """Test UI component rendering"""

    def setup_method(self):
        """Setup for each test"""
        self.output = StringIO()
        self.console = Console(file=self.output, force_terminal=True, width=80)

    def test_panel_render(self):
        """Test panel rendering"""
        panel = Panel(console=self.console)
        panel.render("Test content", title="Test Panel")

        output = self.output.getvalue()
        assert "Test content" in output
        assert "Test Panel" in output

    def test_table_render(self):
        """Test table rendering"""
        table = Table(console=self.console)
        table.render(title="Test Table", columns=["Col1", "Col2"], rows=[["A", "B"], ["C", "D"]])

        output = self.output.getvalue()
        assert "Col1" in output
        assert "Col2" in output

    def test_code_block_render(self):
        """Test code block rendering"""
        code_block = CodeBlock(console=self.console)
        code_block.render("print('hello')", language="python")

        output = self.output.getvalue()
        assert "print" in output

    def test_status_indicator_success(self):
        """Test success indicator"""
        status = StatusIndicator(console=self.console)
        status.success("Operation successful")

        output = self.output.getvalue()
        assert "Operation successful" in output

    def test_status_indicator_error(self):
        """Test error indicator"""
        status = StatusIndicator(console=self.console)
        status.error("Operation failed")

        output = self.output.getvalue()
        assert "Operation failed" in output

    def test_status_indicator_warning(self):
        """Test warning indicator"""
        status = StatusIndicator(console=self.console)
        status.warning("Be careful")

        output = self.output.getvalue()
        assert "Be careful" in output

    def test_status_indicator_info(self):
        """Test info indicator"""
        status = StatusIndicator(console=self.console)
        status.info("Information")

        output = self.output.getvalue()
        assert "Information" in output

    def test_message_box(self):
        """Test message box rendering"""
        msg_box = MessageBox(console=self.console)
        msg_box.show("Test message", title="Test", msg_type="info")

        output = self.output.getvalue()
        assert "Test message" in output


class TestStreamingOutput:
    """Test streaming output functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.output = StringIO()
        self.console = Console(file=self.output, force_terminal=True, width=80)

    def test_stream_simple(self):
        """Test simple streaming"""
        streamer = StreamingOutput(console=self.console, render_markdown=False)

        def token_generator():
            yield "Hello"
            yield " "
            yield "World"

        result = streamer.stream(token_generator(), prefix="AI:")
        assert result == "Hello World"

    def test_stream_with_callback(self):
        """Test streaming with callback"""
        streamer = StreamingOutput(console=self.console)
        callback_called = []

        def on_complete(text):
            callback_called.append(text)

        def token_generator():
            yield "Test"

        streamer.stream(token_generator(), on_complete=on_complete)
        assert len(callback_called) == 1
        assert callback_called[0] == "Test"


class TestStreamManager:
    """Test stream manager"""

    def setup_method(self):
        """Setup for each test"""
        self.output = StringIO()
        self.console = Console(file=self.output, force_terminal=True, width=80)

    def test_create_stream(self):
        """Test creating a stream"""
        manager = StreamManager(console=self.console)
        stream = manager.create_stream("stream1", title="Test Stream")

        assert "stream1" in manager.active_streams
        assert isinstance(stream, StreamingOutput)

    def test_close_stream(self):
        """Test closing a stream"""
        manager = StreamManager(console=self.console)
        manager.create_stream("stream1")

        manager.close_stream("stream1")
        assert "stream1" not in manager.active_streams

    def test_close_all_streams(self):
        """Test closing all streams"""
        manager = StreamManager(console=self.console)
        manager.create_stream("stream1")
        manager.create_stream("stream2")

        manager.close_all()
        assert len(manager.active_streams) == 0


class TestTheme:
    """Test theme system"""

    def test_theme_creation(self):
        """Test creating a theme"""
        theme = Theme(
            name="test",
            primary="blue",
            secondary="cyan",
            success="green",
            error="red",
            warning="yellow",
            info="blue",
            text="white",
            dim="dim white",
            border="blue",
        )

        assert theme.name == "test"
        assert theme.primary == "blue"

    def test_theme_to_rich_theme(self):
        """Test converting to Rich theme"""
        theme = Theme(
            name="test",
            primary="blue",
            secondary="cyan",
            success="green",
            error="red",
            warning="yellow",
            info="blue",
            text="white",
            dim="dim white",
            border="blue",
        )

        rich_theme = theme.to_rich_theme()
        assert rich_theme is not None


class TestThemeManager:
    """Test theme manager"""

    def test_get_builtin_theme(self):
        """Test getting built-in theme"""
        manager = ThemeManager()
        theme = manager.get_theme("default")

        assert theme.name == "default"

    def test_set_theme(self):
        """Test setting active theme"""
        manager = ThemeManager()
        manager.set_theme("dark")

        assert manager.current_theme_name == "dark"

    def test_set_invalid_theme(self):
        """Test error on invalid theme"""
        manager = ThemeManager()

        with pytest.raises(ValueError, match="Theme .* not found"):
            manager.set_theme("nonexistent")

    def test_register_custom_theme(self):
        """Test registering custom theme"""
        manager = ThemeManager()

        custom_theme = Theme(
            name="custom",
            primary="magenta",
            secondary="purple",
            success="green",
            error="red",
            warning="yellow",
            info="cyan",
            text="white",
            dim="dim white",
            border="magenta",
        )

        manager.register_theme(custom_theme)
        assert "custom" in manager.list_themes()

    def test_list_themes(self):
        """Test listing all themes"""
        manager = ThemeManager()
        themes = manager.list_themes()

        assert "default" in themes
        assert "dark" in themes
        assert "light" in themes

    def test_create_console_with_theme(self):
        """Test creating themed console"""
        manager = ThemeManager()
        console = manager.create_console("ocean")

        assert console is not None
        # Console object exists and is functional
