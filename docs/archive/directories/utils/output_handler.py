"""
Platform-Aware Output Handler
==============================

Handles cross-platform output with emoji fallbacks and UTF-8 support.
Prevents UnicodeEncodeError on Windows terminals.

Author: PromptOps Team
Date: 2026-05-11
"""

import sys
import io
import os
from typing import Optional


class PlatformOutput:
    """
    Platform-aware output handler.

    Features:
    - Auto UTF-8 encoding on Windows
    - Emoji fallback for incompatible terminals
    - Safe print functions
    - Progress indicators
    """

    # Emoji mappings with text fallbacks
    EMOJI_MAP = {
        'check': {'emoji': '✅', 'text': '[OK]'},
        'cross': {'emoji': '❌', 'text': '[ERROR]'},
        'rocket': {'emoji': '🚀', 'text': '[INFO]'},
        'warning': {'emoji': '⚠️', 'text': '[WARN]'},
        'info': {'emoji': 'ℹ️', 'text': '[INFO]'},
        'clock': {'emoji': '⏰', 'text': '[TIME]'},
        'package': {'emoji': '📦', 'text': '[PKG]'},
        'wrench': {'emoji': '🔧', 'text': '[TOOL]'},
        'gear': {'emoji': '⚙️', 'text': '[CONFIG]'},
        'fire': {'emoji': '🔥', 'text': '[HOT]'},
        'sparkles': {'emoji': '✨', 'text': '[NEW]'},
        'construction': {'emoji': '🚧', 'text': '[WIP]'},
        'tada': {'emoji': '🎉', 'text': '[DONE]'},
        'arrow_right': {'emoji': '→', 'text': '->'},
        'arrow_down': {'emoji': '↓', 'text': '|'},
    }

    def __init__(self, use_emoji: Optional[bool] = None):
        """
        Initialize output handler.

        Args:
            use_emoji: Force emoji usage (True/False), None for auto-detect
        """
        self.is_windows = sys.platform == 'win32'
        self.use_emoji = self._detect_emoji_support() if use_emoji is None else use_emoji

        # Setup UTF-8 encoding on Windows
        if self.is_windows:
            self._setup_windows_utf8()

    def _setup_windows_utf8(self):
        """Setup UTF-8 encoding for Windows terminal."""
        try:
            # Set console to UTF-8 mode
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            else:
                # Fallback for older Python versions
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
        except Exception:
            # If UTF-8 setup fails, disable emojis
            self.use_emoji = False

    def _detect_emoji_support(self) -> bool:
        """
        Detect if terminal supports emoji.

        Returns:
            True if emoji supported, False otherwise
        """
        # Check environment variables
        term = os.environ.get('TERM', '')
        colorterm = os.environ.get('COLORTERM', '')

        # Modern terminals usually support emoji
        if 'xterm' in term or 'truecolor' in colorterm or '256color' in term:
            return True

        # Windows Terminal supports emoji
        if self.is_windows and os.environ.get('WT_SESSION'):
            return True

        # VSCode integrated terminal
        if os.environ.get('VSCODE_GIT_IPC_HANDLE'):
            return True

        # Default to text on Windows, emoji on Unix
        return not self.is_windows

    def get_icon(self, name: str) -> str:
        """
        Get icon (emoji or text) by name.

        Args:
            name: Icon name from EMOJI_MAP

        Returns:
            Emoji or text fallback
        """
        icon_data = self.EMOJI_MAP.get(name, {'emoji': '', 'text': ''})
        return icon_data['emoji'] if self.use_emoji else icon_data['text']

    def print(self, *args, icon: Optional[str] = None, **kwargs):
        """
        Safe print with optional icon.

        Args:
            *args: Arguments to print
            icon: Icon name from EMOJI_MAP
            **kwargs: Additional print kwargs
        """
        try:
            if icon:
                icon_str = self.get_icon(icon)
                print(icon_str, *args, **kwargs)
            else:
                print(*args, **kwargs)
        except UnicodeEncodeError:
            # Fallback: strip non-ASCII characters
            message = ' '.join(str(arg) for arg in args)
            ascii_message = message.encode('ascii', 'replace').decode('ascii')
            print(ascii_message, **kwargs)

    def print_success(self, message: str):
        """Print success message."""
        self.print(message, icon='check')

    def print_error(self, message: str):
        """Print error message."""
        self.print(message, icon='cross')

    def print_warning(self, message: str):
        """Print warning message."""
        self.print(message, icon='warning')

    def print_info(self, message: str):
        """Print info message."""
        self.print(message, icon='info')

    def print_progress(self, current: int, total: int, prefix: str = ''):
        """
        Print progress bar.

        Args:
            current: Current progress
            total: Total items
            prefix: Prefix text
        """
        percent = int((current / total) * 100) if total > 0 else 0
        bar_length = 40
        filled = int((bar_length * current) / total) if total > 0 else 0

        if self.use_emoji:
            bar = '█' * filled + '░' * (bar_length - filled)
        else:
            bar = '=' * filled + '-' * (bar_length - filled)

        self.print(f'\r{prefix} [{bar}] {percent}% ({current}/{total})', end='', flush=True)

        if current >= total:
            self.print()  # New line when complete

    def print_separator(self, char: str = '=', length: int = 70):
        """
        Print separator line.

        Args:
            char: Character to use
            length: Line length
        """
        self.print(char * length)

    def print_header(self, title: str, icon: Optional[str] = 'rocket'):
        """
        Print formatted header.

        Args:
            title: Header title
            icon: Icon name
        """
        self.print_separator()
        self.print(f"  {title}", icon=icon)
        self.print_separator()

    def format_status(self, status: str) -> str:
        """
        Format status text with icon.

        Args:
            status: Status string (success, error, warning, info)

        Returns:
            Formatted status with icon
        """
        status_map = {
            'success': 'check',
            'error': 'cross',
            'warning': 'warning',
            'info': 'info',
        }
        icon = status_map.get(status.lower(), 'info')
        return f"{self.get_icon(icon)} {status}"

    def clear_line(self):
        """Clear current line (for progress updates)."""
        if self.is_windows:
            print('\r' + ' ' * 100 + '\r', end='', flush=True)
        else:
            print('\033[2K\r', end='', flush=True)


# Global instance
_output = None


def get_output() -> PlatformOutput:
    """Get global output handler instance."""
    global _output
    if _output is None:
        _output = PlatformOutput()
    return _output


def print_safe(*args, **kwargs):
    """Safe print function (module-level convenience)."""
    get_output().print(*args, **kwargs)


def print_success(message: str):
    """Print success message (module-level convenience)."""
    get_output().print_success(message)


def print_error(message: str):
    """Print error message (module-level convenience)."""
    get_output().print_error(message)


def print_warning(message: str):
    """Print warning message (module-level convenience)."""
    get_output().print_warning(message)


def print_info(message: str):
    """Print info message (module-level convenience)."""
    get_output().print_info(message)


# Example usage
if __name__ == "__main__":
    output = PlatformOutput()

    output.print_header("Platform Output Handler Test")
    print()

    output.print_success("This is a success message")
    output.print_error("This is an error message")
    output.print_warning("This is a warning message")
    output.print_info("This is an info message")
    print()

    output.print("Testing all icons:")
    for icon_name in output.EMOJI_MAP.keys():
        output.print(f"  {icon_name}: {output.get_icon(icon_name)}")
    print()

    output.print("Testing progress bar:")
    import time
    for i in range(11):
        output.print_progress(i, 10, "Building")
        time.sleep(0.1)
    print()

    output.print_success("All tests passed!")
