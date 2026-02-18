# Changelog

## [1.0.5] - 2026-02-18

### Fixed
- Remove build artifacts from git repository
- Add .gitignore for deb/rpm artifacts
- Add Transifex translation notice

## [1.0.0] - 2026-02-14

### Added
- Initial release
- Convert between 16+ localization formats
- Compile PO→MO, TS→QM
- Extract translatable strings from Python, C/C++, JavaScript/TypeScript, QML
- Validate: missing translations, placeholder mismatches, duplicate keys
- Translation statistics
- Merge two localization files
- Diff between files
- Initialize new language files from templates
- Auto-detect input format
- Batch processing (recursive directories)
- Pipe support (stdin/stdout)
- `--dry-run` for all commands
- Colored terminal output (rich)
- Plural forms handling
