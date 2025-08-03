"""
Streaming Utilities for Paper-QA
Provides real-time response streaming and callback management.
"""

import sys
import time
from typing import List, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text


class StreamingCallback:
    """Base class for streaming callbacks."""

    def __init__(self):
        self.buffer = ""
        self.start_time = time.time()

    def __call__(self, chunk: str) -> None:
        """Process a chunk of text."""
        self.buffer += chunk
        self.process_chunk(chunk)

    def process_chunk(self, chunk: str) -> None:
        """Override this method to handle chunks."""
        pass

    def get_buffer(self) -> str:
        """Get the complete buffer."""
        return self.buffer

    def get_duration(self) -> float:
        """Get the duration since start."""
        return time.time() - self.start_time


class ConsoleStreamingCallback(StreamingCallback):
    """Stream to console with real-time updates."""

    def __init__(self, console: Optional[Console] = None):
        super().__init__()
        self.console = console or Console()

    def process_chunk(self, chunk: str) -> None:
        """Print chunk to console."""
        self.console.print(chunk, end="", highlight=False)
        sys.stdout.flush()


class RichStreamingCallback(StreamingCallback):
    """Stream with rich formatting and progress indicators."""

    def __init__(self, console: Optional[Console] = None):
        super().__init__()
        self.console = console or Console()
        self.live = None
        self.progress = None

    def process_chunk(self, chunk: str) -> None:
        """Update rich display with chunk."""
        if self.live is None:
            self._start_live_display()

        # Update the live display
        panel = Panel(
            Text(self.buffer, style="white"),
            title="Paper-QA Response",
            border_style="blue",
        )
        self.live.update(panel)

    def _start_live_display(self):
        """Start the live display."""
        self.live = Live(
            Panel("Initializing...", title="Paper-QA Response"),
            console=self.console,
            refresh_per_second=10,
        )
        self.live.start()

    def stop(self):
        """Stop the live display."""
        if self.live:
            self.live.stop()


class ProgressStreamingCallback(StreamingCallback):
    """Stream with progress bar and status updates."""

    def __init__(self, console: Optional[Console] = None):
        super().__init__()
        self.console = console or Console()
        self.progress = None
        self.task = None

    def process_chunk(self, chunk: str) -> None:
        """Update progress with chunk."""
        if self.progress is None:
            self._start_progress()

        # Update progress description
        if self.task:
            self.task.update(description=f"Processing... ({len(self.buffer)} chars)")

    def _start_progress(self):
        """Start the progress display."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )
        self.progress.start()
        self.task = self.progress.add_task("Initializing...", total=None)

    def stop(self):
        """Stop the progress display."""
        if self.progress:
            self.progress.stop()


class FileStreamingCallback(StreamingCallback):
    """Stream to file with timestamps."""

    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename
        self.file = open(filename, "w")

    def process_chunk(self, chunk: str) -> None:
        """Write chunk to file."""
        timestamp = time.strftime("%H:%M:%S")
        self.file.write(f"[{timestamp}] {chunk}")
        self.file.flush()

    def stop(self):
        """Close the file."""
        if self.file:
            self.file.close()


class MultiStreamingCallback:
    """Combine multiple streaming callbacks."""

    def __init__(self, callbacks: List[StreamingCallback]):
        self.callbacks = callbacks

    def __call__(self, chunk: str) -> None:
        """Call all callbacks with the chunk."""
        for callback in self.callbacks:
            callback(chunk)

    def stop(self):
        """Stop all callbacks."""
        for callback in self.callbacks:
            if hasattr(callback, "stop"):
                callback.stop()


def create_streaming_callbacks(
    console: bool = True,
    rich: bool = False,
    progress: bool = False,
    file: Optional[str] = None,
) -> List[StreamingCallback]:
    """Create a list of streaming callbacks based on options."""
    callbacks = []

    if console:
        callbacks.append(ConsoleStreamingCallback())

    if rich:
        callbacks.append(RichStreamingCallback())

    if progress:
        callbacks.append(ProgressStreamingCallback())

    if file:
        callbacks.append(FileStreamingCallback(file))

    return callbacks


def create_multi_callback(
    console: bool = True,
    rich: bool = False,
    progress: bool = False,
    file: Optional[str] = None,
) -> MultiStreamingCallback:
    """Create a multi-callback that combines multiple streaming methods."""
    callbacks = create_streaming_callbacks(console, rich, progress, file)
    return MultiStreamingCallback(callbacks)


class ResponseStreamer:
    """Manages streaming responses with multiple output methods."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.callbacks = []

    def add_callback(self, callback: StreamingCallback) -> None:
        """Add a streaming callback."""
        self.callbacks.append(callback)

    def add_console_callback(self) -> None:
        """Add console streaming callback."""
        self.add_callback(ConsoleStreamingCallback(self.console))

    def add_rich_callback(self) -> None:
        """Add rich streaming callback."""
        self.add_callback(RichStreamingCallback(self.console))

    def add_progress_callback(self) -> None:
        """Add progress streaming callback."""
        self.add_callback(ProgressStreamingCallback(self.console))

    def add_file_callback(self, filename: str) -> None:
        """Add file streaming callback."""
        self.add_callback(FileStreamingCallback(filename))

    def stream(self, chunk: str) -> None:
        """Stream a chunk to all callbacks."""
        for callback in self.callbacks:
            callback(chunk)

    def stop(self) -> None:
        """Stop all callbacks."""
        for callback in self.callbacks:
            if hasattr(callback, "stop"):
                callback.stop()

    def get_buffers(self) -> List[str]:
        """Get buffers from all callbacks."""
        return [callback.get_buffer() for callback in self.callbacks]


# Convenience functions for common streaming patterns
def stream_to_console(chunk: str) -> None:
    """Simple console streaming."""
    callback = ConsoleStreamingCallback()
    callback(chunk)


def stream_with_progress(chunk: str) -> None:
    """Stream with progress indicator."""
    callback = ProgressStreamingCallback()
    callback(chunk)


def stream_to_file(chunk: str, filename: str) -> None:
    """Stream to file."""
    callback = FileStreamingCallback(filename)
    callback(chunk)
    callback.stop()
