"""Java .properties format handler."""

from __future__ import annotations

import re

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("properties")
class PropertiesFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        catalog = TranslationCatalog()
        comment_buf = []

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n\r")
                stripped = line.strip()

                if not stripped or stripped.startswith("#") or stripped.startswith("!"):
                    if stripped.startswith("#") or stripped.startswith("!"):
                        comment_buf.append(stripped[1:].strip())
                    continue

                m = re.match(r"^([^=:]+?)\s*[=:]\s*(.*)", line)
                if m:
                    key = m.group(1).strip()
                    value = m.group(2)
                    state = EntryState.TRANSLATED if value else EntryState.UNTRANSLATED
                    entry = TranslationEntry(
                        key=key,
                        source=key,
                        target=value,
                        state=state,
                        comment="\n".join(comment_buf),
                    )
                    catalog.entries.append(entry)
                    comment_buf = []

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in catalog.entries:
                if entry.comment:
                    for line in entry.comment.split("\n"):
                        f.write(f"# {line}\n")
                value = entry.target or entry.source or ""
                f.write(f"{entry.key}={value}\n")
