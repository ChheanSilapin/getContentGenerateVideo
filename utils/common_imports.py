"""
Common imports module for Video Generator
Provides centralized access to frequently used modules
"""

# Standard library imports used across multiple files
import os
import sys
import subprocess
import tempfile
import traceback
import time
import shutil
import glob
import threading
import json
import platform
import re
from datetime import datetime

# UI imports (tkinter) used across UI components
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import tkinter.font as tkFont
import tkinter.simpledialog

# Re-export for easy access
__all__ = [
    # Standard library
    'os', 'sys', 'subprocess', 'tempfile', 'traceback', 'time',
    'shutil', 'glob', 'threading', 'json', 'datetime', 'platform', 're',
    # UI components
    'tk', 'messagebox', 'ttk', 'filedialog', 'tkFont', 'tkinter'
]