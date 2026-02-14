"""Base class for format handlers."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Optional

from ..model import TranslationCatalog


class BaseFormat(ABC):
    format_name: str = ""

    @abstractmethod
    def read(self, filepath: str) -> TranslationCatalog:
        """Read a file and return a TranslationCatalog."""

    @abstractmethod
    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        """Write a TranslationCatalog to a file."""

    def read_string(self, content: str) -> TranslationCatalog:
        """Read from string content. Default: write to temp file."""
        import tempfile, os
        ext = {"po": ".po", "json": ".json", "yaml": ".yml"}.get(self.format_name, ".tmp")
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            return self.read(tmp)
        finally:
            os.unlink(tmp)

    def write_string(self, catalog: TranslationCatalog) -> str:
        """Write to string. Default: write to temp file."""
        import tempfile, os
        ext = {"po": ".po", "json": ".json", "yaml": ".yml"}.get(self.format_name, ".tmp")
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
            tmp = f.name
        try:
            self.write(catalog, tmp)
            with open(tmp, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            os.unlink(tmp)

    def read_stdin(self) -> TranslationCatalog:
        content = sys.stdin.read()
        return self.read_string(content)

    def write_stdout(self, catalog: TranslationCatalog) -> None:
        sys.stdout.write(self.write_string(catalog))
