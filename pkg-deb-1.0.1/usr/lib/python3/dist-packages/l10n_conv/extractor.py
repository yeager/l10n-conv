"""Extract translatable strings from source code."""

from __future__ import annotations

import os
import re
from typing import List, Tuple

from .model import TranslationCatalog, TranslationEntry, EntryState

# Patterns for different languages
PATTERNS = {
    ".py": [
        re.compile(r"""_\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""gettext\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""ngettext\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]\s*"""),
    ],
    ".c": [
        re.compile(r"""_\(\s*"([^"]+)"\s*\)"""),
        re.compile(r"""gettext\(\s*"([^"]+)"\s*\)"""),
        re.compile(r"""ngettext\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*"""),
        re.compile(r"""N_\(\s*"([^"]+)"\s*\)"""),
    ],
    ".cpp": None,  # same as .c
    ".h": None,  # same as .c
    ".js": [
        re.compile(r"""(?:__|t|i18n\.t)\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""(?:__|t|i18n\.t)\(\s*`([^`]+)`\s*\)"""),
    ],
    ".ts": None,  # same as .js
    ".jsx": None,
    ".tsx": None,
    ".qml": [
        re.compile(r"""qsTr\(\s*"([^"]+)"\s*\)"""),
        re.compile(r"""qsTranslate\(\s*"[^"]+"\s*,\s*"([^"]+)"\s*\)"""),
        re.compile(r"""QT_TR_NOOP\(\s*"([^"]+)"\s*\)"""),
    ],
}

# Alias extensions
PATTERNS[".cpp"] = PATTERNS[".c"]
PATTERNS[".h"] = PATTERNS[".c"]
PATTERNS[".ts"] = PATTERNS[".js"]
PATTERNS[".jsx"] = PATTERNS[".js"]
PATTERNS[".tsx"] = PATTERNS[".js"]


def extract_from_file(filepath: str) -> List[Tuple[str, str, int]]:
    """Extract (string, plural_or_empty, line_number) from a file."""
    ext = os.path.splitext(filepath)[1].lower()
    patterns = PATTERNS.get(ext)
    if not patterns:
        return []

    results = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, 1):
                for pat in patterns:
                    for m in pat.finditer(line):
                        groups = m.groups()
                        msgid = groups[0]
                        plural = groups[1] if len(groups) > 1 else ""
                        results.append((msgid, plural, lineno))
    except (OSError, UnicodeDecodeError):
        pass

    return results


def extract_from_directory(directory: str) -> TranslationCatalog:
    """Recursively extract translatable strings."""
    catalog = TranslationCatalog()
    seen = {}

    for root, dirs, files in os.walk(directory):
        # Skip hidden dirs and common non-source dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".git")]
        for fname in sorted(files):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in PATTERNS:
                continue
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, directory)
            for msgid, plural, lineno in extract_from_file(fpath):
                ref = f"{relpath}:{lineno}"
                key = (msgid, plural)
                if key in seen:
                    seen[key].references.append(ref)
                else:
                    entry = TranslationEntry(
                        key=msgid,
                        source=msgid,
                        state=EntryState.UNTRANSLATED,
                        references=[ref],
                    )
                    if plural:
                        entry.plural_source = plural
                    seen[key] = entry
                    catalog.entries.append(entry)

    return catalog
