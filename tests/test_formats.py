"""Tests for format handlers."""

import os
import json
import pytest

from l10n_conv.model import TranslationCatalog, TranslationEntry, EntryState
from l10n_conv.registry import get_format, detect_format


class TestPOFormat:
    def test_read(self, sample_po):
        fmt = get_format("po")()
        cat = fmt.read(sample_po)
        assert len(cat.entries) == 3
        assert cat.entries[0].target == "Hej"
        assert cat.entries[1].state == EntryState.FUZZY
        assert cat.entries[2].state == EntryState.UNTRANSLATED

    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.po")
        fmt = get_format("po")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)
        assert cat2.entries[0].target == "Hej"

    def test_write_mo(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.mo")
        fmt = get_format("mo")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        # MO excludes fuzzy entries but includes untranslated
        non_fuzzy = [e for e in sample_catalog.entries if e.state != EntryState.FUZZY]
        assert len(cat2.entries) == len(non_fuzzy)


class TestJsonFormat:
    def test_read(self, sample_json):
        fmt = get_format("json")()
        cat = fmt.read(sample_json)
        assert len(cat.entries) == 3

    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.json")
        fmt = get_format("json")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)

    def test_nested(self, tmp_dir):
        path = os.path.join(tmp_dir, "nested.json")
        with open(path, "w") as f:
            json.dump({"app": {"title": "My App", "desc": "Description"}}, f)
        fmt = get_format("json")()
        cat = fmt.read(path)
        assert len(cat.entries) == 2
        assert cat.entries[0].key == "app.title"


class TestPropertiesFormat:
    def test_read(self, sample_properties):
        fmt = get_format("properties")()
        cat = fmt.read(sample_properties)
        assert len(cat.entries) == 2
        assert cat.entries[0].target == "Hej"

    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.properties")
        fmt = get_format("properties")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestYamlFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.yml")
        fmt = get_format("yaml")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)
        assert cat2.target_language == "sv"


class TestXliffFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.xlf")
        fmt = get_format("xliff")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)
        assert cat2.entries[0].target == "Hej"


class TestAndroidXmlFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "strings.xml")
        fmt = get_format("android-xml")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestStringsFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "Localizable.strings")
        fmt = get_format("strings")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestCsvFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.csv")
        fmt = get_format("csv")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestArbFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.arb")
        fmt = get_format("arb")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestFluentFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.ftl")
        fmt = get_format("fluent")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestResxFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.resx")
        fmt = get_format("resx")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestTmxFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.tmx")
        fmt = get_format("tmx")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestPhpFormat:
    def test_roundtrip(self, sample_catalog, tmp_dir):
        path = os.path.join(tmp_dir, "out.php")
        fmt = get_format("php")()
        fmt.write(sample_catalog, path)
        cat2 = fmt.read(path)
        assert len(cat2.entries) == len(sample_catalog.entries)


class TestDetectFormat:
    def test_detect_po(self, sample_po):
        assert detect_format(sample_po) == "po"

    def test_detect_json(self, sample_json):
        assert detect_format(sample_json) == "json"

    def test_detect_properties(self, sample_properties):
        assert detect_format(sample_properties) == "properties"


class TestConversion:
    """Test cross-format conversion."""

    def test_po_to_json(self, sample_po, tmp_dir):
        po_fmt = get_format("po")()
        json_fmt = get_format("json")()
        cat = po_fmt.read(sample_po)
        out = os.path.join(tmp_dir, "out.json")
        json_fmt.write(cat, out)
        cat2 = json_fmt.read(out)
        assert len(cat2.entries) == len(cat.entries)

    def test_json_to_yaml(self, sample_json, tmp_dir):
        json_fmt = get_format("json")()
        yaml_fmt = get_format("yaml")()
        cat = json_fmt.read(sample_json)
        out = os.path.join(tmp_dir, "out.yml")
        yaml_fmt.write(cat, out)
        cat2 = yaml_fmt.read(out)
        assert len(cat2.entries) == len(cat.entries)

    def test_po_to_xliff(self, sample_po, tmp_dir):
        po_fmt = get_format("po")()
        xliff_fmt = get_format("xliff")()
        cat = po_fmt.read(sample_po)
        out = os.path.join(tmp_dir, "out.xlf")
        xliff_fmt.write(cat, out)
        cat2 = xliff_fmt.read(out)
        assert len(cat2.entries) == len(cat.entries)
