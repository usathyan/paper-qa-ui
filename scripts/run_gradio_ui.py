#!/usr/bin/env python3
"""
Script to run the PaperQA2 Gradio UI with proper environment setup.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperqa2_ui import main

if __name__ == "__main__":
    main()
