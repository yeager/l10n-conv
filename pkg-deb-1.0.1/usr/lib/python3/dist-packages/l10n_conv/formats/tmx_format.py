"""TMX (Translation Memory eXchange) format handler."""

from __future__ import annotations

from lxml import etree

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("tmx")
class TmxFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        tree = etree.parse(filepath)
        root = tree.getroot()
        catalog = TranslationCatalog()

        header = root.find(".//header")
        if header is not None:
            catalog.source_language = header.get("srclang", "")
            catalog.metadata["datatype"] = header.get("datatype", "")

        for tu in root.iter("tu"):
            tuid = tu.get("tuid", "")
            tuvs = tu.findall("tuv")
            source = ""
            target = ""
            src_lang = ""
            tgt_lang = ""

            for tuv in tuvs:
                lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang", "") or tuv.get("lang", "")
                seg = tuv.find("seg")
                text = seg.text if seg is not None and seg.text else ""
                if not source:
                    source = text
                    src_lang = lang
                else:
                    target = text
                    tgt_lang = lang

            if not catalog.source_language and src_lang:
                catalog.source_language = src_lang
            if not catalog.target_language and tgt_lang:
                catalog.target_language = tgt_lang

            state = EntryState.TRANSLATED if target else EntryState.UNTRANSLATED
            catalog.entries.append(TranslationEntry(
                key=tuid or source, source=source, target=target, state=state,
            ))

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        root = etree.Element("tmx", version="1.4")
        header = etree.SubElement(root, "header")
        header.set("srclang", catalog.source_language or "en")
        header.set("datatype", catalog.metadata.get("datatype", "plaintext"))
        header.set("segtype", "sentence")
        header.set("adminlang", "en")
        header.set("creationtool", "l10n-conv")
        header.set("creationtoolversion", "1.0.0")

        body = etree.SubElement(root, "body")
        for entry in catalog.entries:
            tu = etree.SubElement(body, "tu")
            if entry.key:
                tu.set("tuid", entry.key)

            tuv_src = etree.SubElement(tu, "tuv")
            tuv_src.set("{http://www.w3.org/XML/1998/namespace}lang", catalog.source_language or "en")
            seg_src = etree.SubElement(tuv_src, "seg")
            seg_src.text = entry.source or entry.key

            if entry.target:
                tuv_tgt = etree.SubElement(tu, "tuv")
                tuv_tgt.set("{http://www.w3.org/XML/1998/namespace}lang", catalog.target_language or "und")
                seg_tgt = etree.SubElement(tuv_tgt, "seg")
                seg_tgt.text = entry.target

        tree = etree.ElementTree(root)
        tree.write(filepath, xml_declaration=True, encoding="utf-8", pretty_print=True)
