"""JSON format handler (i18next, Chrome, Mozilla, flat)."""

from __future__ import annotations

import json

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("json")
class JsonFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        catalog = TranslationCatalog()
        self._flatten(data, "", catalog)
        return catalog

    def _flatten(self, data, prefix: str, catalog: TranslationCatalog):
        if isinstance(data, dict):
            for key, val in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(val, str):
                    state = EntryState.TRANSLATED if val else EntryState.UNTRANSLATED
                    catalog.entries.append(TranslationEntry(
                        key=full_key, source=full_key, target=val, state=state,
                    ))
                elif isinstance(val, dict):
                    # Check if it's an i18next plural object
                    if any(k in val for k in ("one", "other", "zero", "two", "few", "many")):
                        te = TranslationEntry(
                            key=full_key, source=full_key, state=EntryState.TRANSLATED,
                            plural_source=full_key,
                        )
                        qty_map = {"zero": 0, "one": 1, "two": 2, "few": 3, "many": 4, "other": 5}
                        for k, v in val.items():
                            if k in qty_map:
                                te.plural_targets[qty_map[k]] = v
                        catalog.entries.append(te)
                    else:
                        self._flatten(val, full_key, catalog)
                elif isinstance(val, dict):
                    # Chrome extension format: {"message": "...", "description": "..."}
                    if "message" in val:
                        catalog.entries.append(TranslationEntry(
                            key=full_key, source=full_key,
                            target=val["message"],
                            state=EntryState.TRANSLATED,
                            comment=val.get("description", ""),
                        ))
                    else:
                        self._flatten(val, full_key, catalog)

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        data = {}
        for entry in catalog.entries:
            keys = entry.key.split(".")
            d = data
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            if entry.is_plural:
                qty_names = {0: "zero", 1: "one", 2: "two", 3: "few", 4: "many", 5: "other"}
                d[keys[-1]] = {qty_names[i]: v for i, v in entry.plural_targets.items()}
            else:
                d[keys[-1]] = entry.target or ""

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
