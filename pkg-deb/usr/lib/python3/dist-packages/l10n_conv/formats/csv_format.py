"""CSV/TSV format handler."""

from __future__ import annotations

import csv

from ..model import TranslationCatalog, TranslationEntry, EntryState
from ..registry import register_format
from .base import BaseFormat


class _CsvBase(BaseFormat):
    delimiter = ","

    def read(self, filepath: str) -> TranslationCatalog:
        catalog = TranslationCatalog()
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            header = next(reader, None)
            # Expect: key, source, target [, comment, context]
            for row in reader:
                if not row:
                    continue
                key = row[0] if len(row) > 0 else ""
                source = row[1] if len(row) > 1 else key
                target = row[2] if len(row) > 2 else ""
                comment = row[3] if len(row) > 3 else ""
                context = row[4] if len(row) > 4 else ""
                state = EntryState.TRANSLATED if target else EntryState.UNTRANSLATED
                catalog.entries.append(TranslationEntry(
                    key=key, source=source, target=target, state=state,
                    comment=comment, context=context,
                ))
        return catalog

    def write(self, catalog: TranslationCatalog, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=self.delimiter)
            writer.writerow(["key", "source", "target", "comment", "context"])
            for entry in catalog.entries:
                writer.writerow([
                    entry.key, entry.source, entry.target,
                    entry.comment, entry.context,
                ])


@register_format("csv")
class CsvFormat(_CsvBase):
    delimiter = ","


@register_format("tsv")
class TsvFormat(_CsvBase):
    delimiter = "\t"
