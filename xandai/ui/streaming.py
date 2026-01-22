"""
Streaming Output

Real-time streaming output handler for AI responses.
"""

import sys
import time
from typing import Callable, Iterator, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text


class StreamingOutput:
    """
    Streaming output handler

    Renders AI output in real-time with formatting.
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        render_markdown: bool = True,
        show_cursor: bool = True,
    ):
        """
        Initialize streaming output

        Args:
            console: Rich console
            render_markdown: Auto-render markdown
            show_cursor: Show typing cursor
        """
        self.console = console or Console()
        self.render_markdown = render_markdown
        self.show_cursor = show_cursor
        self.buffer = []

    def stream(
        self,
        tokens: Iterator[str],
        prefix: str = "",
        on_complete: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Stream tokens to output

        Args:
            tokens: Token iterator from LLM
            prefix: Prefix to show before content
            on_complete: Callback when streaming completes

        Returns:
            Complete generated text
        """
        self.buffer = []

        if prefix:
            self.console.print(f"[bold cyan]{prefix}[/bold cyan]")

        # Use Live for smooth updates
        with Live("", console=self.console, refresh_per_second=30) as live:
            for token in tokens:
                self.buffer.append(token)
                current_text = "".join(self.buffer)

                # Render with cursor
                if self.show_cursor:
                    display_text = current_text + "▋"
                else:
                    display_text = current_text

                # Update display
                if self.render_markdown:
                    try:
                        live.update(Markdown(display_text))
                    except:
                        live.update(Text(display_text))
                else:
                    live.update(Text(display_text))

        # Final render without cursor
        final_text = "".join(self.buffer)

        self.console.print()  # New line

        if on_complete:
            on_complete(final_text)

        return final_text

    def stream_simple(self, tokens: Iterator[str]) -> str:
        """
        Simple streaming without formatting

        Args:
            tokens: Token iterator

        Returns:
            Complete text
        """
        result = []

        for token in tokens:
            result.append(token)
            sys.stdout.write(token)
            sys.stdout.flush()

        sys.stdout.write("\n")
        return "".join(result)


class StreamManager:
    """
    Stream Manager

    Manages multiple concurrent streams (future feature).
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize stream manager

        Args:
            console: Rich console
        """
        self.console = console or Console()
        self.active_streams = {}

    def create_stream(self, stream_id: str, title: Optional[str] = None) -> StreamingOutput:
        """
        Create a new stream

        Args:
            stream_id: Unique stream ID
            title: Stream title

        Returns:
            StreamingOutput instance
        """
        if title:
            self.console.print(f"[bold blue]{title}[/bold blue]")

        stream = StreamingOutput(console=self.console)
        self.active_streams[stream_id] = stream

        return stream

    def close_stream(self, stream_id: str):
        """Close a stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]

    def close_all(self):
        """Close all active streams"""
        self.active_streams.clear()
