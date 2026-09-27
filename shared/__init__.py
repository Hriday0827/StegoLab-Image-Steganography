"""
shared/__init__.py
-------------------
Reusable utilities across all StegoLab phases.
Configures UTF-8 console output for cross-platform compatibility.
"""

import sys

def configure_utf8_stdout():
    """Ensure standard output and standard error support UTF-8 on Windows."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

configure_utf8_stdout()
