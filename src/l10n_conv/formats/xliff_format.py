"""XLIFF 1.2/2.0 format handler."""

from __future__ import annotations

from lxml import etree

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat

NS12 = "urn:oasis:names:tc:xliff:document:1.2"
NS20 = "urn:oasis:names:tc:xliff:document:2.0"


@register_format("xliff")
class XliffFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        tree = etree.parse(filepath)
        root = tree.getroot()
        tag = root.tag
        catalog = TranslationCatalog()

        if NS20 in tag:
            return self._read_v2(root, catalog)
        return self._read_v1(root, catalog)

    def _read_v1(self, root, catalog: TranslationCatalog) -> TranslationCatalog:
        ns = {"x": NS12}
        for file_el in root.findall(".//x:file", ns):
            catalog.source_language = file_el.get("source-language", "")
            catalog.target_language = file_el.get("target-language", "")
            for unit in file_el.findall(".//x:trans-unit", ns):
                src_el = unit.find("x:source", ns)
                tgt_el = unit.find("x:target", ns)
                note_el = unit.find("x:note", ns)

                source = src_el.text if src_el is not None and src_el.text else ""
                target = tgt_el.text if tgt_el is not None and tgt_el.text else ""

                state = EntryState.UNTRANSLATED
                if tgt_el is not None:
                    st = tgt_el.get("state", "")
                    if st == "final" or st == "translated":
                        state = EntryState.TRANSLATED
                    elif st == "needs-translation" or st == "needs-review-translation":
                        state = EntryState.FUZZY
                    elif target:
                        state = EntryState.TRANSLATED

                catalog.entries.append(TranslationEntry(
                    key=unit.get("id", source),
                    source=source,
                    target=target,
                    state=state,
                    comment=note_el.text if note_el is not None and note_el.text else "",
                ))
        return catalog

    def _read_v2(self, root, catalog: TranslationCatalog) -> TranslationCatalog:
        catalog.source_language = root.get("srcLang", "")
        catalog.target_language = root.get("trgLang", "")
        ns = {"x": NS20}
        for unit in root.findall(".//x:unit", ns):
            seg = unit.find(".//x:segment", ns)
            if seg is None:
                continue
            src_el = seg.find("x:source", ns)
            tgt_el = seg.find("x:target", ns)

            source = src_el.text if src_el is not None and src_el.text else ""
            target = tgt_el.text if tgt_el is not None and tgt_el.text else ""
            state_attr = seg.get("state", "initial")

            state = EntryState.UNTRANSLATED
            if state_attr == "final" or state_attr == "translated":
                state = EntryState.TRANSLATED
            elif state_attr == "reviewed":
                state = EntryState.TRANSLATED
            elif target:
                state = EntryState.TRANSLATED

            notes = unit.find("x:notes", ns)
            comment = ""
            if notes is not None:
                note = notes.find("x:note", ns)
                if note is not None and note.text:
                    comment = note.text

            catalog.entries.append(TranslationEntry(
                key=unit.get("id", source),
                source=source,
                target=target,
                state=state,
                comment=comment,
            ))
        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        # Write XLIFF 1.2
        nsmap = {None: NS12}
        root = etree.Element("{%s}xliff" % NS12, nsmap=nsmap, version="1.2")
        file_el = etree.SubElement(root, "file")
        file_el.set("source-language", catalog.source_language or "en")
        if catalog.target_language:
            file_el.set("target-language", catalog.target_language)
        file_el.set("datatype", "plaintext")
        file_el.set("original", "l10n-conv")

        body = etree.SubElement(file_el, "body")

        for i, entry in enumerate(catalog.entries):
            unit = etree.SubElement(body, "trans-unit")
            unit.set("id", entry.key or str(i + 1))

            src = etree.SubElement(unit, "source")
            src.text = entry.source or entry.key

            tgt = etree.SubElement(unit, "target")
            tgt.text = entry.target
            if entry.state == EntryState.TRANSLATED:
                tgt.set("state", "translated")
            elif entry.state == EntryState.FUZZY:
                tgt.set("state", "needs-translation")
            else:
                tgt.set("state", "new")

            if entry.comment:
                note = etree.SubElement(unit, "note")
                note.text = entry.comment

        tree = etree.ElementTree(root)
        tree.write(filepath, xml_declaration=True, encoding="utf-8", pretty_print=True)
