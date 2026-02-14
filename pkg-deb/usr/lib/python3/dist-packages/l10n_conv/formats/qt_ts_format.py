"""Qt .ts (XML) format handler."""

from __future__ import annotations

from lxml import etree

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


@register_format("qt-ts")
class QtTsFormat(BaseFormat):
    def read(self, filepath: str) -> TranslationCatalog:
        tree = etree.parse(filepath)
        root = tree.getroot()
        catalog = TranslationCatalog(
            target_language=root.get("language", ""),
            source_language=root.get("sourcelanguage", ""),
        )

        for context_el in root.iter("context"):
            ctx_name = ""
            name_el = context_el.find("name")
            if name_el is not None and name_el.text:
                ctx_name = name_el.text

            for msg in context_el.iter("message"):
                source_el = msg.find("source")
                trans_el = msg.find("translation")
                comment_el = msg.find("comment")

                source = source_el.text if source_el is not None and source_el.text else ""
                target = ""
                state = EntryState.UNTRANSLATED

                if trans_el is not None:
                    t_type = trans_el.get("type", "")
                    if t_type == "unfinished":
                        state = EntryState.FUZZY
                    elif t_type == "obsolete":
                        state = EntryState.OBSOLETE
                        continue

                    # Check for numerusform (plurals)
                    numerus = trans_el.findall("numerusform")
                    if numerus:
                        state = EntryState.TRANSLATED
                        te = TranslationEntry(
                            key=source,
                            source=source,
                            context=ctx_name,
                            state=state,
                            comment=comment_el.text if comment_el is not None and comment_el.text else "",
                        )
                        te.plural_source = source
                        for i, nf in enumerate(numerus):
                            te.plural_targets[i] = nf.text or ""
                        catalog.entries.append(te)
                        continue

                    target = trans_el.text or ""
                    if target and state != EntryState.FUZZY:
                        state = EntryState.TRANSLATED

                te = TranslationEntry(
                    key=source,
                    source=source,
                    target=target,
                    state=state,
                    context=ctx_name,
                    comment=comment_el.text if comment_el is not None and comment_el.text else "",
                )

                loc_el = msg.find("location")
                if loc_el is not None:
                    filename = loc_el.get("filename", "")
                    line = loc_el.get("line", "")
                    if filename:
                        te.references.append(f"{filename}:{line}" if line else filename)

                catalog.entries.append(te)

        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        root = etree.Element("TS", version="2.1")
        if catalog.target_language:
            root.set("language", catalog.target_language)
        if catalog.source_language:
            root.set("sourcelanguage", catalog.source_language)

        contexts: dict[str, etree._Element] = {}

        for entry in catalog.entries:
            ctx_name = entry.context or "default"
            if ctx_name not in contexts:
                ctx_el = etree.SubElement(root, "context")
                name_el = etree.SubElement(ctx_el, "name")
                name_el.text = ctx_name
                contexts[ctx_name] = ctx_el

            msg = etree.SubElement(contexts[ctx_name], "message")

            if entry.references:
                ref = entry.references[0]
                loc = etree.SubElement(msg, "location")
                if ":" in ref:
                    parts = ref.rsplit(":", 1)
                    loc.set("filename", parts[0])
                    loc.set("line", parts[1])
                else:
                    loc.set("filename", ref)

            src = etree.SubElement(msg, "source")
            src.text = entry.source or entry.key

            if entry.comment:
                c = etree.SubElement(msg, "comment")
                c.text = entry.comment

            trans = etree.SubElement(msg, "translation")
            if entry.is_plural:
                for i in sorted(entry.plural_targets.keys()):
                    nf = etree.SubElement(trans, "numerusform")
                    nf.text = entry.plural_targets[i]
            else:
                if entry.state == EntryState.FUZZY:
                    trans.set("type", "unfinished")
                elif entry.state == EntryState.UNTRANSLATED:
                    trans.set("type", "unfinished")
                trans.text = entry.target

        tree = etree.ElementTree(root)
        tree.write(filepath, xml_declaration=True, encoding="utf-8", pretty_print=True)
