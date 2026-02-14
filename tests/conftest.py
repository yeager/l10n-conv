"""Test fixtures."""

import os
import pytest
import tempfile

from l10n_conv.model import TranslationCatalog, TranslationEntry, EntryState


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_catalog():
    cat = TranslationCatalog(
        source_language="en",
        target_language="sv",
    )
    cat.entries = [
        TranslationEntry(key="hello", source="Hello", target="Hej", state=EntryState.TRANSLATED),
        TranslationEntry(key="goodbye", source="Goodbye", target="Hejdå", state=EntryState.TRANSLATED),
        TranslationEntry(key="untranslated", source="Not yet", target="", state=EntryState.UNTRANSLATED),
        TranslationEntry(key="fuzzy_one", source="Maybe", target="Kanske", state=EntryState.FUZZY),
    ]
    return cat


@pytest.fixture
def sample_po(tmp_dir):
    path = os.path.join(tmp_dir, "test.po")
    with open(path, "w", encoding="utf-8") as f:
        f.write('''
msgid ""
msgstr ""
"Language: sv\\n"
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello"
msgstr "Hej"

#, fuzzy
msgid "Maybe"
msgstr "Kanske"

msgid "Untranslated"
msgstr ""
''')
    return path


@pytest.fixture
def sample_json(tmp_dir):
    path = os.path.join(tmp_dir, "test.json")
    with open(path, "w") as f:
        f.write('{"hello": "Hej", "goodbye": "Hejdå", "empty": ""}')
    return path


@pytest.fixture
def sample_properties(tmp_dir):
    path = os.path.join(tmp_dir, "test.properties")
    with open(path, "w") as f:
        f.write("hello=Hej\ngoodbye=Hejdå\n")
    return path
