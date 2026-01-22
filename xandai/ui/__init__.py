"""
XandAI UI Components

Terminal UI components for a beautiful CLI experience.
"""

from xandai.ui.components import (
    CodeBlock,
    MessageBox,
    Panel,
    ProgressBar,
    Spinner,
    StatusIndicator,
    Table,
)
from xandai.ui.streaming import StreamingOutput, StreamManager
from xandai.ui.theme import Theme, ThemeManager

__all__ = [
    "Panel",
    "Table",
    "ProgressBar",
    "Spinner",
    "CodeBlock",
    "StatusIndicator",
    "MessageBox",
    "StreamingOutput",
    "StreamManager",
    "Theme",
    "ThemeManager",
]
