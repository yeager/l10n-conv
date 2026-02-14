"""Gettext MO (compiled) format handler."""

from __future__ import annotations

import polib

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("mo")
class MOFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        mo = polib.mofile(filepath)
        catalog = TranslationCatalog(
            target_language=mo.metadata.get("Language", ""),
        )
        catalog.metadata = dict(mo.metadata)
        for entry in mo:
            state = EntryState.TRANSLATED if entry.msgstr else EntryState.UNTRANSLATED
            te = TranslationEntry(
                key=entry.msgid,
                source=entry.msgid,
                target=entry.msgstr,
                state=state,
                context=entry.msgctxt or "",
            )
            if entry.msgid_plural:
                te.plural_source = entry.msgid_plural
                te.plural_targets = dict(entry.msgstr_plural) if entry.msgstr_plural else {}
            catalog.entries.append(te)
        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        mo = polib.MOFile()
        mo.metadata = catalog.metadata.copy() if catalog.metadata else {}
        if catalog.target_language:
            mo.metadata["Language"] = catalog.target_language

        for entry in catalog.entries:
            if entry.state == EntryState.FUZZY:
                continue  # Fuzzy entries excluded from MO
            pe = polib.POEntry(
                msgid=entry.source or entry.key,
                msgstr=entry.target,
                msgctxt=entry.context or None,
            )
            if entry.is_plural:
                pe.msgid_plural = entry.plural_source
                pe.msgstr_plural = entry.plural_targets
            mo.append(pe)

        mo.save(filepath)
