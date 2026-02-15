"""Android strings.xml format handler."""

from __future__ import annotations

from lxml import etree

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("android-xml")
class AndroidXmlFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        tree = etree.parse(filepath)
        root = tree.getroot()
        catalog = TranslationCatalog()

        for el in root:
            if el.tag == "string":
                name = el.get("name", "")
                text = el.text or ""
                state = EntryState.TRANSLATED if text else EntryState.UNTRANSLATED
                comment = ""
                prev = el.getprevious()
                if prev is not None and isinstance(prev, etree._Comment):
                    comment = prev.text.strip() if prev.text else ""
                catalog.entries.append(TranslationEntry(
                    key=name, source=name, target=text, state=state, comment=comment,
                ))
            elif el.tag == "plurals":
                name = el.get("name", "")
                te = TranslationEntry(
                    key=name, source=name, state=EntryState.TRANSLATED,
                    plural_source=name,
                )
                for item in el.findall("item"):
                    q = item.get("quantity", "other")
                    qty_map = {"zero": 0, "one": 1, "two": 2, "few": 3, "many": 4, "other": 5}
                    te.plural_targets[qty_map.get(q, 5)] = item.text or ""
                catalog.entries.append(te)
            elif el.tag == "string-array":
                name = el.get("name", "")
                for i, item in enumerate(el.findall("item")):
                    catalog.entries.append(TranslationEntry(
                        key=f"{name}[{i}]",
                        source=f"{name}[{i}]",
                        target=item.text or "",
                        state=EntryState.TRANSLATED if item.text else EntryState.UNTRANSLATED,
                    ))

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        root = etree.Element("resources")

        for entry in catalog.entries:
            if entry.comment:
                root.append(etree.Comment(f" {entry.comment} "))

            if entry.is_plural:
                pl = etree.SubElement(root, "plurals", name=entry.key)
                qty_names = {0: "zero", 1: "one", 2: "two", 3: "few", 4: "many", 5: "other"}
                for i in sorted(entry.plural_targets.keys()):
                    item = etree.SubElement(pl, "item", quantity=qty_names.get(i, "other"))
                    item.text = entry.plural_targets[i]
            else:
                el = etree.SubElement(root, "string", name=entry.key)
                el.text = entry.target or ""

        tree = etree.ElementTree(root)
        tree.write(filepath, xml_declaration=True, encoding="utf-8", pretty_print=True)
