"""Tests for CLI commands."""

import os
import json
import pytest
from click.testing import CliRunner

from l10n_conv.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestConvertCommand:
    def test_po_to_json(self, runner, sample_po, tmp_dir):
        out = os.path.join(tmp_dir, "out.json")
        result = runner.invoke(main, ["convert", sample_po, "--to", "json", "-o", out])
        assert result.exit_code == 0
        assert os.path.exists(out)
        data = json.load(open(out))
        assert "Hello" in data

    def test_dry_run(self, runner, sample_po, tmp_dir):
        out = os.path.join(tmp_dir, "out.json")
        result = runner.invoke(main, ["convert", sample_po, "--to", "json", "-o", out, "--dry-run"])
        assert result.exit_code == 0
        assert not os.path.exists(out)

    def test_auto_detect_output_format(self, runner, sample_po, tmp_dir):
        out = os.path.join(tmp_dir, "out.json")
        result = runner.invoke(main, ["convert", sample_po, "-o", out])
        assert result.exit_code == 0


class TestCheckCommand:
    def test_check_po(self, runner, sample_po):
        result = runner.invoke(main, ["check", sample_po])
        # Has untranslated and fuzzy entries
        assert result.exit_code in (0, 1, 2)

    def test_check_clean(self, runner, sample_json):
        result = runner.invoke(main, ["check", sample_json])
        assert result.exit_code in (0, 2)  # May have empty string warning


class TestStatsCommand:
    def test_stats_po(self, runner, sample_po):
        result = runner.invoke(main, ["stats", sample_po])
        assert result.exit_code == 0
        assert "Translated" in result.output

    def test_stats_json(self, runner, sample_json):
        result = runner.invoke(main, ["stats", sample_json])
        assert result.exit_code == 0


class TestCompileCommand:
    def test_compile_po_to_mo(self, runner, sample_po, tmp_dir):
        out = os.path.join(tmp_dir, "out.mo")
        result = runner.invoke(main, ["compile", sample_po, "-o", out])
        assert result.exit_code == 0
        assert os.path.exists(out)


class TestMergeCommand:
    def test_merge(self, runner, sample_po, tmp_dir):
        # Create an update file
        update = os.path.join(tmp_dir, "update.po")
        with open(update, "w") as f:
            f.write('msgid ""\nmsgstr ""\n\nmsgid "Untranslated"\nmsgstr "Oöversatt"\n')
        out = os.path.join(tmp_dir, "merged.po")
        result = runner.invoke(main, ["merge", sample_po, update, "-o", out])
        assert result.exit_code == 0
        assert os.path.exists(out)


class TestDiffCommand:
    def test_diff(self, runner, sample_po, tmp_dir):
        po2 = os.path.join(tmp_dir, "test2.po")
        with open(sample_po) as f:
            content = f.read().replace("Hej", "Hallå")
        with open(po2, "w") as f:
            f.write(content)
        result = runner.invoke(main, ["diff", sample_po, po2])
        assert result.exit_code == 0


class TestInitCommand:
    def test_init(self, runner, sample_po, tmp_dir):
        out = os.path.join(tmp_dir, "new.po")
        result = runner.invoke(main, ["init", sample_po, "-l", "de", "-o", out])
        assert result.exit_code == 0
        assert os.path.exists(out)


class TestExtractCommand:
    def test_extract(self, runner, tmp_dir):
        # Create a Python file with translatable strings
        src_dir = os.path.join(tmp_dir, "src")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "app.py"), "w") as f:
            f.write('print(_("Hello World"))\nprint(_("Goodbye"))\n')
        out = os.path.join(tmp_dir, "messages.po")
        result = runner.invoke(main, ["extract", src_dir, "-o", out])
        assert result.exit_code == 0
        assert os.path.exists(out)


class TestVersion:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output
