"""Core data model for localization entries."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class EntryState(enum.Enum):
    TRANSLATED = "translated"
    UNTRANSLATED = "untranslated"
    FUZZY = "fuzzy"
    OBSOLETE = "obsolete"


@dataclass
class TranslationEntry:
    """A single translatable unit."""
    key: str
    source: str = ""
    target: str = ""
    state: EntryState = EntryState.UNTRANSLATED
    context: str = ""
    comment: str = ""
    translator_comment: str = ""
    references: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    plural_source: str = ""
    plural_targets: Dict[int, str] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def is_plural(self) -> bool:
        return bool(self.plural_source or self.plural_targets)

    @property
    def is_translated(self) -> bool:
        if self.is_plural:
            return bool(self.plural_targets)
        return bool(self.target)


@dataclass
class TranslationCatalog:
    """A collection of translation entries (one file)."""
    entries: List[TranslationEntry] = field(default_factory=list)
    source_language: str = ""
    target_language: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    comments: List[str] = field(default_factory=list)
    plural_forms: str = ""

    @property
    def translated_count(self) -> int:
        return sum(1 for e in self.entries if e.state == EntryState.TRANSLATED)

    @property
    def untranslated_count(self) -> int:
        return sum(1 for e in self.entries if e.state == EntryState.UNTRANSLATED)

    @property
    def fuzzy_count(self) -> int:
        return sum(1 for e in self.entries if e.state == EntryState.FUZZY)

    @property
    def completion_percent(self) -> float:
        total = len(self.entries)
        if not total:
            return 100.0
        return round(self.translated_count / total * 100, 1)

    def get_entry(self, key: str, context: str = "") -> Optional[TranslationEntry]:
        for e in self.entries:
            if e.key == key and e.context == context:
                return e
        return None
