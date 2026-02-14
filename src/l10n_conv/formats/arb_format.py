"""ARB (Application Resource Bundle / Flutter) format handler."""

from __future__ import annotations

import json

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("arb")
class ArbFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        catalog = TranslationCatalog()
        catalog.target_language = data.get("@@locale", "")
        catalog.metadata = {k: v for k, v in data.items() if k.startswith("@@")}

        for key, value in data.items():
            if key.startswith("@@") or key.startswith("@"):
                continue
            if not isinstance(value, str):
                continue

            comment = ""
            meta_key = f"@{key}"
            if meta_key in data and isinstance(data[meta_key], dict):
                comment = data[meta_key].get("description", "")

            state = EntryState.TRANSLATED if value else EntryState.UNTRANSLATED
            catalog.entries.append(TranslationEntry(
                key=key, source=key, target=value, state=state, comment=comment,
            ))

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        data = {}
        if catalog.target_language:
            data["@@locale"] = catalog.target_language
        for k, v in catalog.metadata.items():
            if k.startswith("@@"):
                data[k] = v

        for entry in catalog.entries:
            data[entry.key] = entry.target or ""
            if entry.comment:
                data[f"@{entry.key}"] = {"description": entry.comment}

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
