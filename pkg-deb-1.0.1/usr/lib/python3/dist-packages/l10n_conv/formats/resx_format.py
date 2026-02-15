"""Windows .resx format handler."""

from __future__ import annotations

from lxml import etree

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("resx")
class ResxFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        tree = etree.parse(filepath)
        root = tree.getroot()
        catalog = TranslationCatalog()

        for data_el in root.findall("data"):
            name = data_el.get("name", "")
            val_el = data_el.find("value")
            comment_el = data_el.find("comment")
            value = val_el.text if val_el is not None and val_el.text else ""
            comment = comment_el.text if comment_el is not None and comment_el.text else ""
            state = EntryState.TRANSLATED if value else EntryState.UNTRANSLATED
            catalog.entries.append(TranslationEntry(
                key=name, source=name, target=value, state=state, comment=comment,
            ))

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        root = etree.Element("root")
        # Standard resx headers
        for name in ("resmimetype", "version", "reader", "writer"):
            rh = etree.SubElement(root, "resheader", name=name)
            val = etree.SubElement(rh, "value")
            if name == "resmimetype":
                val.text = "text/microsoft-resx"
            elif name == "version":
                val.text = "2.0"
            elif name == "reader":
                val.text = "System.Resources.ResXResourceReader"
            elif name == "writer":
                val.text = "System.Resources.ResXResourceWriter"

        for entry in catalog.entries:
            data = etree.SubElement(root, "data")
            data.set("name", entry.key)
            data.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            val = etree.SubElement(data, "value")
            val.text = entry.target or ""
            if entry.comment:
                c = etree.SubElement(data, "comment")
                c.text = entry.comment

        tree = etree.ElementTree(root)
        tree.write(filepath, xml_declaration=True, encoding="utf-8", pretty_print=True)
