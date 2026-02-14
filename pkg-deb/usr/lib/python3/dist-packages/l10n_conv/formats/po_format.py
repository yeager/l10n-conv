"""Gettext PO/POT format handler."""

from __future__ import annotations

import polib

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("po")
class POFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        po = polib.pofile(filepath)
        catalog = TranslationCatalog(
            target_language=po.metadata.get("Language", ""),
            plural_forms=po.metadata.get("Plural-Forms", ""),
        )
        catalog.metadata = dict(po.metadata)

        for entry in po:
            if entry.obsolete:
                continue
            state = EntryState.UNTRANSLATED
            if "fuzzy" in entry.flags:
                state = EntryState.FUZZY
            elif entry.msgstr or entry.msgstr_plural:
                state = EntryState.TRANSLATED

            te = TranslationEntry(
                key=entry.msgid,
                source=entry.msgid,
                target=entry.msgstr,
                state=state,
                context=entry.msgctxt or "",
                comment=entry.comment or "",
                translator_comment=entry.tcomment or "",
                references=[f"{r[0]}:{r[1]}" for r in entry.occurrences],
                flags=[f for f in entry.flags if f != "fuzzy"],
            )
            if entry.msgid_plural:
                te.plural_source = entry.msgid_plural
                te.plural_targets = dict(entry.msgstr_plural) if entry.msgstr_plural else {}
            catalog.entries.append(te)

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        po = polib.POFile()
        po.metadata = catalog.metadata.copy() if catalog.metadata else {}
        if catalog.target_language:
            po.metadata["Language"] = catalog.target_language
        if catalog.plural_forms:
            po.metadata["Plural-Forms"] = catalog.plural_forms
        po.metadata.setdefault("Content-Type", "text/plain; charset=UTF-8")
        po.metadata.setdefault("Content-Transfer-Encoding", "8bit")

        for entry in catalog.entries:
            flags = list(entry.flags)
            if entry.state == EntryState.FUZZY and "fuzzy" not in flags:
                flags.insert(0, "fuzzy")

            occ = []
            for ref in entry.references:
                if ":" in ref:
                    parts = ref.rsplit(":", 1)
                    occ.append((parts[0], parts[1]))
                else:
                    occ.append((ref, ""))

            pe = polib.POEntry(
                msgid=entry.source or entry.key,
                msgstr=entry.target,
                msgctxt=entry.context or None,
                comment=entry.comment,
                tcomment=entry.translator_comment,
                occurrences=occ,
                flags=flags,
            )
            if entry.is_plural:
                pe.msgid_plural = entry.plural_source
                pe.msgstr_plural = entry.plural_targets
            po.append(pe)

        po.save(filepath)
