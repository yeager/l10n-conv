"""Format registry and auto-detection."""

from __future__ import annotations

import os
from typing import Dict, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .formats.base import BaseFormat

_FORMAT_REGISTRY: Dict[str, Type["BaseFormat"]] = {}

# Extension to format name mapping
_EXT_MAP: Dict[str, str] = {
    ".po": "po",
    ".pot": "po",
    ".mo": "mo",
    ".ts": "qt-ts",
    ".qm": "qm",
    ".xlf": "xliff",
    ".xliff": "xliff",
    ".properties": "properties",
    ".xml": "android-xml",
    ".strings": "strings",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".csv": "csv",
    ".tsv": "tsv",
    ".tmx": "tmx",
    ".tbx": "tbx",
    ".php": "php",
    ".arb": "arb",
    ".ftl": "fluent",
    ".rc": "rc",
    ".resx": "resx",
}


def register_format(name: str):
    """Decorator to register a format handler."""
    def decorator(cls):
        _FORMAT_REGISTRY[name] = cls
        cls.format_name = name
        return cls
    return decorator


def get_format(name: str) -> Type["BaseFormat"]:
    _ensure_loaded()
    if name not in _FORMAT_REGISTRY:
        raise ValueError(f"Unknown format: {name}. Available: {', '.join(sorted(_FORMAT_REGISTRY))}")
    return _FORMAT_REGISTRY[name]


def detect_format(filepath: str) -> Optional[str]:
    """Detect format from file extension and content."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".xml":
        # Peek to distinguish android strings.xml from other XML
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                head = f.read(500)
            if "<resources" in head:
                return "android-xml"
            if "<tmx" in head:
                return "tmx"
            if "<martif" in head or "<tbx" in head:
                return "tbx"
            if "<TS" in head:
                return "qt-ts"
            if "<xliff" in head:
                return "xliff"
        except Exception:
            pass
        return "android-xml"
    if ext == ".json":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                head = f.read(200)
            if '"@@locale"' in head or '"@@last_modified"' in head:
                return "arb"
        except Exception:
            pass
        return "json"
    return _EXT_MAP.get(ext)


def list_formats():
    _ensure_loaded()
    return sorted(_FORMAT_REGISTRY.keys())


_loaded = False

def _ensure_loaded():
    global _loaded
    if _loaded:
        return
    _loaded = True
    from .formats import (  # noqa: F401
        po_format, mo_format, qt_ts_format, xliff_format,
        properties_format, android_xml_format, strings_format,
        json_format, yaml_format, csv_format, tmx_format,
        tbx_format, php_format, arb_format, fluent_format,
        resx_format,
    )
