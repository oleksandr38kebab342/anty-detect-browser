"""Compatibility shim for database imports.

This module preserves legacy imports while delegating to the modular
database package.
"""
from __future__ import annotations

import os

# Expose package path so that `database.db_handler` can be imported
__path__ = [os.path.join(os.path.dirname(__file__), "database")]

from database.db_handler import Database, save_profile  # noqa: E402

__all__ = ["Database", "save_profile"]
