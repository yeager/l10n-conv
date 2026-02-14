"""Fluent (.ftl) format handler."""

from __future__ import annotations

import re

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("fluent")
class FluentFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        catalog = TranslationCatalog()
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        comment_buf = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("##"):
                comment_buf.append(stripped.lstrip("# "))
                continue

            m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*)\s*=\s*(.*)", line)
            if m:
                key = m.group(1)
                value = m.group(2).strip()
                state = EntryState.TRANSLATED if value else EntryState.UNTRANSLATED
                catalog.entries.append(TranslationEntry(
                    key=key, source=key, target=value, state=state,
                    comment="\n".join(comment_buf),
                ))
                comment_buf = []
            elif not stripped:
                comment_buf = []

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            for i, entry in enumerate(catalog.entries):
                if entry.comment:
                    for line in entry.comment.split("\n"):
                        f.write(f"# {line}\n")
                f.write(f"{entry.key} = {entry.target or ''}\n")
                if i < len(catalog.entries) - 1:
                    f.write("\n")
