# l10n-conv

![Version](https://img.shields.io/badge/version-1.0.9-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)

## Description

Universal localization file converter, validator, and compiler — **lupdate + lrelease for all l10n formats**. l10n-conv provides seamless conversion between different translation file formats, making it easy to migrate projects or work with multiple translation tools.

This professional-grade CLI tool supports 16+ localization formats and offers robust conversion, validation, and compilation capabilities essential for modern internationalization workflows.

## Features

- **16+ format support**: PO, TS, XLIFF, JSON, YAML, Android XML, iOS Strings, ARB, and more
- **Bidirectional conversion**: Convert between any supported formats
- **Validation**: Built-in format validation and error checking
- **Compilation**: Compile source formats to binary/optimized versions
- **Auto-detection**: Automatic format detection from file extensions
- **Rich CLI**: Beautiful terminal output with progress bars and colors
- **Extensible**: Modular design for adding new formats
- **Production-ready**: Comprehensive error handling and logging

## Installation

### APT (Debian/Ubuntu) - Recommended
```bash
echo "deb https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager-l10n.list
curl -fsSL https://yeager.github.io/debian-repo/yeager-l10n.gpg | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/yeager-l10n.gpg
sudo apt update && sudo apt install l10n-conv
```

### DNF (Fedora)
```bash
sudo dnf config-manager --add-repo https://yeager.github.io/rpm-repo/yeager-l10n.repo
sudo dnf install l10n-conv
```

## Troubleshooting

### ModuleNotFoundError: No module named 'l10n_conv.formats'

If you encounter this error after a system update, reinstall the package:

```bash
# For APT systems (recommended fix)
sudo apt reinstall l10n-conv

# If reinstall doesn't work
sudo apt remove l10n-conv
sudo apt install l10n-conv

# Verify the fix worked
l10n-conv --help
```

This issue typically occurs after:
- Python environment changes
- Incomplete package updates
- System upgrades affecting Python modules

The reinstall process will properly restore all required modules and dependencies.

### pip
```bash
pip install l10n-conv
```

## Building from source

```bash
git clone https://github.com/yeager/l10n-conv
cd l10n-conv
pip install -e .
```

## Usage

Convert between formats:
```bash
# Convert PO to XLIFF
l10n-conv convert input.po output.xliff

# Auto-detect formats
l10n-conv convert translations.json translations.po

# Validate files
l10n-conv validate translations.po

# Compile to binary
l10n-conv compile messages.po messages.mo
```

### Format Support

| Format | Extension | Read | Write | Compile |
|--------|-----------|------|-------|---------|
| GNU gettext PO | `.po` | ✓ | ✓ | → `.mo` |
| Qt Linguist | `.ts` | ✓ | ✓ | → `.qm` |
| XLIFF | `.xliff` | ✓ | ✓ | - |
| JSON | `.json` | ✓ | ✓ | - |
| YAML | `.yaml/.yml` | ✓ | ✓ | - |
| Android XML | `.xml` | ✓ | ✓ | - |
| iOS Strings | `.strings` | ✓ | ✓ | - |
| Flutter ARB | `.arb` | ✓ | ✓ | - |

## Changelog

- **1.0.9** (2026-03): Module import fixes, improved error handling
- **1.0.8**: Enhanced format validation and stability improvements
- **1.0.7**: Performance optimizations and new format support
- **1.0.6**: Extended XLIFF support and better auto-detection
- **1.0.5**: Android XML and iOS Strings support added
- **1.0.4**: Stable release with comprehensive format support

## License

GPL-3.0-or-later

## Contributing

Contributions welcome! This tool is actively used in large-scale localization projects.

1. Fork the repository
2. Create a feature branch
3. Add tests for new formats or features
4. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/yeager/l10n-conv/issues)
- **Documentation**: `l10n-conv --help`
- **Package Updates**: Available via Debian/RPM repositories
