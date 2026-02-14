"""Tests for checker."""

from l10n_conv.model import TranslationCatalog, TranslationEntry, EntryState
from l10n_conv.checker import check_catalog


def test_placeholder_mismatch():
    cat = TranslationCatalog(entries=[
        TranslationEntry(key="msg", source="Hello %s", target="Hej", state=EntryState.TRANSLATED),
    ])
    results = check_catalog(cat)
    errors = [r for r in results if r.level == "error" and "Placeholder" in r.message]
    assert len(errors) == 1


def test_duplicate_keys():
    cat = TranslationCatalog(entries=[
        TranslationEntry(key="dup", source="A", target="B", state=EntryState.TRANSLATED),
        TranslationEntry(key="dup", source="C", target="D", state=EntryState.TRANSLATED),
    ])
    results = check_catalog(cat)
    errors = [r for r in results if r.level == "error" and "Duplicate" in r.message]
    assert len(errors) == 1


def test_clean_catalog():
    cat = TranslationCatalog(entries=[
        TranslationEntry(key="ok", source="OK", target="OK", state=EntryState.TRANSLATED),
    ])
    results = check_catalog(cat)
    errors = [r for r in results if r.level == "error"]
    assert len(errors) == 0
