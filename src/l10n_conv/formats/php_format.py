"""PHP array format handler."""

from __future__ import annotations

import re

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("php")
class PhpFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        catalog = TranslationCatalog()
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Match 'key' => 'value' patterns
        for m in re.finditer(
            r"""['"]([^'"]+)['"]\s*=>\s*['"]([^']*(?:(?:\\'|\\")[^'"]*)*)['"]""",
            content
        ):
            key = m.group(1)
            value = m.group(2).replace("\\'", "'").replace('\\"', '"')
            state = EntryState.TRANSLATED if value else EntryState.UNTRANSLATED
            catalog.entries.append(TranslationEntry(
                key=key, source=key, target=value, state=state,
            ))

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("<?php\n\nreturn [\n")
            for entry in catalog.entries:
                key = entry.key.replace("'", "\\'")
                val = (entry.target or "").replace("'", "\\'")
                f.write(f"    '{key}' => '{val}',\n")
            f.write("];\n")
