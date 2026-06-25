"""PROJECT WARROOM - CLI Entry Point

Usage:
    python __main__.py init my-project
    python __main__.py analyze my-project
    python __main__.py judge my-project
"""
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 for Windows console (Rich uses Unicode chars)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from cli.commands import app

if __name__ == "__main__":
    app()
