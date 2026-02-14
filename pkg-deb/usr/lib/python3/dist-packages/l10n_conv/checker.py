"""Validation checks for translation files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from .model import TranslationCatalog, TranslationEntry, EntryState


@dataclass
class CheckResult:
    level: str  # "error", "warning", "info"
    message: str
    key: str = ""
    details: str = ""


def check_catalog(catalog: TranslationCatalog) -> List[CheckResult]:
    results = []

    # Check for missing translations
    for entry in catalog.entries:
        if entry.state == EntryState.UNTRANSLATED:
            results.append(CheckResult("warning", "Missing translation", key=entry.key))

    # Check for duplicate keys
    seen = {}
    for entry in catalog.entries:
        k = (entry.key, entry.context)
        if k in seen:
            results.append(CheckResult("error", "Duplicate key", key=entry.key,
                                       details=f"context={entry.context!r}"))
        seen[k] = True

    # Check placeholder consistency
    placeholder_patterns = [
        re.compile(r"%[sdifcx%]"),          # C-style
        re.compile(r"%\d+\$[sdifcx]"),      # positional C-style
        re.compile(r"\{(\d+|[a-zA-Z_]\w*)\}"),  # Python/Java {0}, {name}
        re.compile(r"\{\{[^}]+\}\}"),         # Angular
        re.compile(r"%@"),                    # Objective-C
    ]

    for entry in catalog.entries:
        if not entry.target or not entry.source:
            continue
        for pat in placeholder_patterns:
            src_matches = sorted(pat.findall(entry.source))
            tgt_matches = sorted(pat.findall(entry.target))
            if src_matches and src_matches != tgt_matches:
                results.append(CheckResult(
                    "error", "Placeholder mismatch", key=entry.key,
                    details=f"source={src_matches} target={tgt_matches}",
                ))
                break

    # Check for fuzzy entries
    for entry in catalog.entries:
        if entry.state == EntryState.FUZZY:
            results.append(CheckResult("info", "Fuzzy translation", key=entry.key))

    return results
