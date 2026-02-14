# l10n-conv

Universal localization file converter, validator, and compiler — **lupdate + lrelease for all l10n formats**.

## Installation

```bash
pip install l10n-conv
```

## Supported Formats

| Format | Extensions | Read | Write |
|--------|-----------|------|-------|
| Gettext PO/POT | `.po`, `.pot` | ✓ | ✓ |
| Gettext MO | `.mo` | ✓ | ✓ |
| Qt TS | `.ts` | ✓ | ✓ |
| XLIFF 1.2/2.0 | `.xlf`, `.xliff` | ✓ | ✓ |
| Java Properties | `.properties` | ✓ | ✓ |
| Android XML | `.xml` | ✓ | ✓ |
| iOS Strings | `.strings` | ✓ | ✓ |
| JSON (i18next/flat) | `.json` | ✓ | ✓ |
| YAML (Rails i18n) | `.yml`, `.yaml` | ✓ | ✓ |
| CSV/TSV | `.csv`, `.tsv` | ✓ | ✓ |
| TMX | `.tmx` | ✓ | ✓ |
| TBX | `.tbx` | ✓ | ✓ |
| PHP arrays | `.php` | ✓ | ✓ |
| ARB (Flutter) | `.arb` | ✓ | ✓ |
| Fluent | `.ftl` | ✓ | ✓ |
| Windows RESX | `.resx` | ✓ | ✓ |

## Usage

### Convert between formats

```bash
# PO → JSON
l10n-conv convert messages.po --to json -o messages.json

# XLIFF → Android XML
l10n-conv convert translations.xlf --to android-xml -o strings.xml

# Auto-detect output format from extension
l10n-conv convert messages.po -o translations.xlf
```

### Compile

```bash
# PO → MO (like msgfmt)
l10n-conv compile messages.po -o messages.mo
```

### Extract strings from source code

```bash
# Extract from Python/JS/C/QML source
l10n-conv extract src/ -o messages.po
```

### Validate

```bash
# Check for issues
l10n-conv check messages.po
```

### Statistics

```bash
l10n-conv stats messages.po
```

### Merge

```bash
# Merge translations (like msgmerge)
l10n-conv merge base.po updates.po -o merged.po
```

### Diff

```bash
l10n-conv diff old.po new.po
```

### Initialize new language

```bash
l10n-conv init template.pot -l sv -o sv.po
```

### Batch processing

```bash
# Convert all files in a directory
l10n-conv convert locale/ --to json -o output/ --batch
```

## Options

- `--dry-run` — Preview without writing
- `-v/--verbose` — Detailed output
- `--batch` — Process directories recursively
- Pipe support: use `-` for stdin/stdout

## Exit Codes

- `0` — Success
- `1` — Error
- `2` — Warnings

## License

GPL-3.0-or-later — Daniel Nylander <daniel@danielnylander.se>
