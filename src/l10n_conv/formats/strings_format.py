"""iOS Localizable.strings format handler."""

from __future__ import annotations

import re

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("strings")
class StringsFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        catalog = TranslationCatalog()
        comment_buf = []

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Match /* comments */ and "key" = "value";
        for m in re.finditer(
            r'(?:/\*\s*(.*?)\s*\*/\s*)?'
            r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;',
            content, re.DOTALL
        ):
            comment = m.group(1) or ""
            key = m.group(2)
            value = m.group(3)
            state = EntryState.TRANSLATED if value else EntryState.UNTRANSLATED
            catalog.entries.append(TranslationEntry(
                key=key, source=key, target=value, state=state, comment=comment.strip(),
            ))

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in catalog.entries:
                if entry.comment:
                    f.write(f"/* {entry.comment} */\n")
                key = entry.key.replace('"', '\\"')
                val = (entry.target or "").replace('"', '\\"')
                f.write(f'"{key}" = "{val}";\n\n')
