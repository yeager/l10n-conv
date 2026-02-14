"""YAML (Rails i18n) format handler."""

from __future__ import annotations

import yaml

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("yaml")
class YamlFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        catalog = TranslationCatalog()

        # Rails format: top-level key is locale
        if len(data) == 1:
            lang = list(data.keys())[0]
            if isinstance(data[lang], dict):
                catalog.target_language = str(lang)
                data = data[lang]

        self._flatten(data, "", catalog)
        return catalog

    def _flatten(self, data, prefix: str, catalog: TranslationCatalog):
        if isinstance(data, dict):
            for key, val in data.items():
                full_key = f"{prefix}.{key}" if prefix else str(key)
                if isinstance(val, str):
                    state = EntryState.TRANSLATED if val else EntryState.UNTRANSLATED
                    catalog.entries.append(TranslationEntry(
                        key=full_key, source=full_key, target=val, state=state,
                    ))
                elif isinstance(val, dict):
                    self._flatten(val, full_key, catalog)
                elif val is not None:
                    catalog.entries.append(TranslationEntry(
                        key=full_key, source=full_key, target=str(val),
                        state=EntryState.TRANSLATED,
                    ))

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        data = {}
        for entry in catalog.entries:
            keys = entry.key.split(".")
            d = data
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = entry.target or ""

        if catalog.target_language:
            data = {catalog.target_language: data}

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
