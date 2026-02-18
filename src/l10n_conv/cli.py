"""CLI entry point for l10n-conv."""

from __future__ import annotations

import gettext
import json
import locale
import os
import sys

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .model import TranslationCatalog, EntryState
from .registry import detect_format, get_format, list_formats

TEXTDOMAIN = "l10n-conv"
LOCALEDIR = "/usr/share/locale"
try:
    locale.bindtextdomain(TEXTDOMAIN, LOCALEDIR)
    locale.textdomain(TEXTDOMAIN)
except AttributeError:
    pass
gettext.bindtextdomain(TEXTDOMAIN, LOCALEDIR)
gettext.textdomain(TEXTDOMAIN)
_ = gettext.gettext

console = Console(stderr=True)
out_console = Console()


def _read_catalog(filepath: str, fmt: str | None = None) -> tuple[TranslationCatalog, str]:
    """Read a catalog, auto-detecting format if needed."""
    if filepath == "-":
        if not fmt:
            raise click.UsageError(_("Format must be specified when reading from stdin (-f/--format)"))
        handler = get_format(fmt)()
        return handler.read_stdin(), fmt

    if not fmt:
        fmt = detect_format(filepath)
        if not fmt:
            raise click.UsageError(_("Cannot detect format of {path}. Use -f/--format.").format(path=filepath))
    handler = get_format(fmt)()
    return handler.read(filepath), fmt


def _write_catalog(catalog: TranslationCatalog, filepath: str, fmt: str) -> None:
    """Write a catalog to file or stdout."""
    handler = get_format(fmt)()
    if filepath == "-":
        handler.write_stdout(catalog)
    else:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        handler.write(catalog, filepath)


def _process_batch(input_path: str, callback, **kwargs):
    """Process files recursively in batch mode."""
    if os.path.isfile(input_path):
        callback(input_path, **kwargs)
    elif os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for f in sorted(files):
                fpath = os.path.join(root, f)
                try:
                    callback(fpath, **kwargs)
                except Exception as e:
                    console.print(f"[yellow]⚠ {_('Skipping {path}: {error}').format(path=fpath, error=e)}[/yellow]")


def _show_about(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"l10n-conv {__version__}")
    click.echo(_("Universal localization file converter, validator, and compiler"))
    click.echo()
    click.echo(f"{_('Author')}:     Daniel Nylander <daniel@danielnylander.se>")
    click.echo(f"{_('License')}:    GPL-3.0-or-later")
    click.echo(f"{_('Website')}:    https://github.com/yeager/l10n-conv")
    click.echo(f"{_('PyPI')}:       https://pypi.org/project/l10n-conv/")
    click.echo(f"{_('Translate')}:  https://app.transifex.com/danielnylander/l10n-conv/")
    ctx.exit()


@click.group(help=_("l10n-conv — Universal localization file converter, validator, and compiler."))
@click.version_option(__version__, prog_name="l10n-conv")
@click.option("--about", is_flag=True, callback=_show_about, expose_value=False, is_eager=True, help=_("Show application info and exit"))
@click.option("-v", "--verbose", is_flag=True, help=_("Verbose output"))
@click.option("-j", "--json", "json_output", is_flag=True, help=_("JSON output"))
@click.option("-q", "--quiet", is_flag=True, help=_("Suppress non-essential output (only errors)"))
@click.pass_context
def main(ctx, verbose, json_output, quiet):
    """l10n-conv — Universal localization file converter, validator, and compiler."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["json"] = json_output
    ctx.obj["quiet"] = quiet


@main.command(help=_("Convert between localization formats."))
@click.argument("input", type=str)
@click.option("-f", "--format", "in_fmt", help=_("Input format"))
@click.option("--to", "out_fmt", help=_("Output format"))
@click.option("-o", "--output", help=_("Output file (- for stdout)"))
@click.option("--dry-run", is_flag=True, help=_("Show what would be done"))
@click.option("--batch", is_flag=True, help=_("Process directory recursively"))
@click.pass_context
def convert(ctx, input, in_fmt, out_fmt, output, dry_run, batch):
    """Convert between localization formats."""
    if not out_fmt and not output:
        raise click.UsageError(_("Specify --to <format> or -o <output>"))

    if not out_fmt and output and output != "-":
        out_fmt = detect_format(output)
        if not out_fmt:
            raise click.UsageError(_("Cannot detect output format from {path}. Use --to.").format(path=output))

    if batch:
        def _conv(fpath, **kw):
            catalog, _det = _read_catalog(fpath, in_fmt)
            if output:
                rel = os.path.relpath(fpath, input)
                base = os.path.splitext(rel)[0]
                ext_map = {f: e for e, f in _get_ext_map().items()}
                ext = ext_map.get(out_fmt, ".out")
                opath = os.path.join(output, base + ext)
            else:
                opath = "-"
            if dry_run:
                console.print(f"[dim]{_('Would convert {src} → {dst}').format(src=fpath, dst=opath)}[/dim]")
                return
            _write_catalog(catalog, opath, out_fmt)
            if ctx.obj.get("verbose"):
                console.print(f"[green]✓[/green] {fpath} → {opath}")

        _process_batch(input, _conv)
        return

    catalog, detected = _read_catalog(input, in_fmt)
    if dry_run:
        console.print(f"[dim]{_('Would convert {src} ({fmt_in}) → {dst} ({fmt_out})').format(src=input, fmt_in=detected, dst=output or 'stdout', fmt_out=out_fmt)}[/dim]")
        console.print(f"[dim]{_('entries').format()} {len(catalog.entries)}[/dim]")
        return

    _write_catalog(catalog, output or "-", out_fmt)
    if ctx.obj.get("verbose"):
        console.print(f"[green]✓[/green] {_('Converted {count} entries from {src} to {dst}').format(count=len(catalog.entries), src=detected, dst=out_fmt)}")


def _get_ext_map():
    from .registry import _EXT_MAP
    return _EXT_MAP


@main.command(help=_("Compile localization files (.po→.mo, .ts→.qm)."))
@click.argument("input", type=str)
@click.option("-o", "--output", required=True, help=_("Output file"))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def compile(ctx, input, output, dry_run):
    """Compile localization files (.po→.mo, .ts→.qm)."""
    fmt = detect_format(input)
    if fmt == "po":
        if dry_run:
            console.print(f"[dim]{_('Would compile {src} → {dst} (PO→MO)').format(src=input, dst=output)}[/dim]")
            return
        catalog, _det = _read_catalog(input, "po")
        _write_catalog(catalog, output, "mo")
        console.print(f"[green]✓[/green] {_('Compiled {src} → {dst}').format(src=input, dst=output)}")
    elif fmt == "qt-ts":
        if dry_run:
            console.print(f"[dim]{_('Would compile {src} → {dst} (TS→QM)').format(src=input, dst=output)}[/dim]")
            return
        import subprocess
        try:
            subprocess.run(["lrelease", input, "-qm", output], check=True, capture_output=True)
            console.print(f"[green]✓[/green] {_('Compiled {src} → {dst}').format(src=input, dst=output)}")
        except FileNotFoundError:
            console.print(f"[red]✗ {_('lrelease not found. Install Qt tools for .ts→.qm compilation.')}[/red]")
            sys.exit(1)
    else:
        console.print(f"[red]✗ {_('Compilation not supported for format: {fmt}').format(fmt=fmt)}[/red]")
        sys.exit(1)


@main.command(help=_("Extract translatable strings from source code."))
@click.argument("source_dir", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help=_("Output file"))
@click.option("-f", "--format", "out_fmt", default="po", help=_("Output format (default: po)"))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def extract(ctx, source_dir, output, out_fmt, dry_run):
    """Extract translatable strings from source code."""
    from .extractor import extract_from_directory

    catalog = extract_from_directory(source_dir)

    if dry_run:
        console.print(f"[dim]{_('Would extract {count} strings → {dst}').format(count=len(catalog.entries), dst=output)}[/dim]")
        return

    _write_catalog(catalog, output, out_fmt)
    console.print(f"[green]✓[/green] {_('Extracted {count} strings → {dst}').format(count=len(catalog.entries), dst=output)}")


@main.command(help=_("Validate a localization file."))
@click.argument("file", type=str)
@click.option("-f", "--format", "fmt", help=_("File format"))
@click.pass_context
def check(ctx, file, fmt):
    """Validate a localization file."""
    from .checker import check_catalog

    catalog, detected = _read_catalog(file, fmt)
    results = check_catalog(catalog)

    json_output = ctx.obj.get("json")
    quiet = ctx.obj.get("quiet")

    errors = warnings = infos = 0
    for r in results:
        if r.level == "error":
            errors += 1
        elif r.level == "warning":
            warnings += 1
        else:
            infos += 1

    if json_output:
        data = {
            "file": file,
            "issues": [{"level": r.level, "message": r.message, "key": r.key,
                         "details": r.details} for r in results],
            "errors": errors,
            "warnings": warnings,
            "info": infos,
        }
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    elif not quiet:
        if not results:
            console.print(f"[green]✓[/green] {file}: {_('No issues found')}")
        else:
            for r in results:
                icon = {"error": "[red]✗[/red]", "warning": "[yellow]⚠[/yellow]", "info": "[blue]ℹ[/blue]"}
                console.print(f"  {icon.get(r.level, '?')} {r.message}: {r.key}" +
                               (f" ({r.details})" if r.details else ""))
            console.print(f"\n{_('errors {e}, warnings {w}, info {i}').format(e=errors, w=warnings, i=infos)}")

    sys.exit(2 if errors else (1 if warnings else 0))


@main.command(help=_("Show translation statistics."))
@click.argument("file", type=str)
@click.option("-f", "--format", "fmt", help=_("File format"))
@click.pass_context
def stats(ctx, file, fmt):
    """Show translation statistics."""
    catalog, detected = _read_catalog(file, fmt)
    json_output = ctx.obj.get("json")
    quiet = ctx.obj.get("quiet")

    if json_output:
        data = {
            "file": file,
            "total": len(catalog.entries),
            "translated": catalog.translated_count,
            "untranslated": catalog.untranslated_count,
            "fuzzy": catalog.fuzzy_count,
            "completion_percent": catalog.completion_percent,
            "language": catalog.target_language,
        }
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    elif not quiet:
        table = Table(title=_("Statistics: {file}").format(file=file))
        table.add_column(_("Metric"), style="bold")
        table.add_column(_("Value"), justify="right")

        total = len(catalog.entries)
        table.add_row(_("Total entries"), str(total))
        table.add_row(_("Translated"), f"[green]{catalog.translated_count}[/green]")
        table.add_row(_("Untranslated"), f"[red]{catalog.untranslated_count}[/red]")
        table.add_row(_("Fuzzy"), f"[yellow]{catalog.fuzzy_count}[/yellow]")
        table.add_row(_("Completion"), f"{catalog.completion_percent}%")
        if catalog.target_language:
            table.add_row(_("Language"), catalog.target_language)

        out_console.print(table)


@main.command(help=_("Merge two localization files (like msgmerge)."))
@click.argument("base", type=str)
@click.argument("update", type=str)
@click.option("-o", "--output", required=True, help=_("Output file"))
@click.option("-f", "--format", "fmt", help=_("File format"))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def merge(ctx, base, update, output, fmt, dry_run):
    """Merge two localization files (like msgmerge)."""
    base_cat, detected = _read_catalog(base, fmt)
    update_cat, _det = _read_catalog(update, fmt or detected)

    update_map = {}
    for entry in update_cat.entries:
        update_map[(entry.key, entry.context)] = entry

    merged = 0
    for entry in base_cat.entries:
        key = (entry.key, entry.context)
        if key in update_map:
            upd = update_map[key]
            if upd.is_translated:
                entry.target = upd.target
                entry.state = upd.state
                entry.plural_targets = upd.plural_targets
                merged += 1

    if dry_run:
        console.print(f"[dim]{_('Would merge {count} translations from {src} into {dst}').format(count=merged, src=update, dst=base)}[/dim]")
        return

    _write_catalog(base_cat, output, fmt or detected)
    console.print(f"[green]✓[/green] {_('Merged {count} translations → {dst}').format(count=merged, dst=output)}")


@main.command(help=_("Show differences between two localization files."))
@click.argument("file1", type=str)
@click.argument("file2", type=str)
@click.option("-f", "--format", "fmt", help=_("File format"))
@click.pass_context
def diff(ctx, file1, file2, fmt):
    """Show differences between two localization files."""
    cat1, detected = _read_catalog(file1, fmt)
    cat2, _det = _read_catalog(file2, fmt or detected)

    map1 = {(e.key, e.context): e for e in cat1.entries}
    map2 = {(e.key, e.context): e for e in cat2.entries}

    all_keys = sorted(set(map1.keys()) | set(map2.keys()))

    json_output = ctx.obj.get("json")
    quiet = ctx.obj.get("quiet")

    added = removed = changed = 0
    changes = []
    for key in all_keys:
        e1 = map1.get(key)
        e2 = map2.get(key)

        if e1 and not e2:
            changes.append({"type": "removed", "key": key[0], "old": e1.target})
            removed += 1
        elif e2 and not e1:
            changes.append({"type": "added", "key": key[0], "new": e2.target})
            added += 1
        elif e1.target != e2.target:
            changes.append({"type": "changed", "key": key[0], "old": e1.target, "new": e2.target})
            changed += 1

    if json_output:
        click.echo(json.dumps({"added": added, "removed": removed, "changed": changed,
                                "changes": changes}, indent=2, ensure_ascii=False))
    elif not quiet:
        for c in changes:
            if c["type"] == "removed":
                console.print(f"[red]- {c['key']}[/red]: {c['old']}")
            elif c["type"] == "added":
                console.print(f"[green]+ {c['key']}[/green]: {c['new']}")
            else:
                console.print(f"[yellow]~ {c['key']}[/yellow]:")
                console.print(f"  [red]- {c['old']}[/red]")
                console.print(f"  [green]+ {c['new']}[/green]")
        console.print(f"\n{_('{added} added, {removed} removed, {changed} changed').format(added=added, removed=removed, changed=changed)}")


@main.command(help=_("Create a new language file from a template."))
@click.argument("template", type=str)
@click.option("-l", "--lang", required=True, help=_("Target language code"))
@click.option("-o", "--output", required=True, help=_("Output file"))
@click.option("-f", "--format", "fmt", help=_("File format"))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def init(ctx, template, lang, output, fmt, dry_run):
    """Create a new language file from a template."""
    catalog, detected = _read_catalog(template, fmt)
    catalog.target_language = lang

    for entry in catalog.entries:
        entry.target = ""
        entry.state = EntryState.UNTRANSLATED
        entry.plural_targets = {}

    if dry_run:
        console.print(f"[dim]{_('Would create {dst} for language {lang} with {count} entries').format(dst=output, lang=lang, count=len(catalog.entries))}[/dim]")
        return

    _write_catalog(catalog, output, fmt or detected)
    console.print(f"[green]✓[/green] {_('Created {dst} for language {lang} with {count} entries').format(dst=output, lang=lang, count=len(catalog.entries))}")


@main.command(name="formats", help=_("List all supported formats."))
@click.pass_context
def list_formats_cmd(ctx):
    """List all supported formats."""
    from .registry import _EXT_MAP
    fmt_exts: dict[str, list[str]] = {}
    for ext, fmt in _EXT_MAP.items():
        fmt_exts.setdefault(fmt, []).append(ext)

    if ctx.obj.get("json"):
        data = {fmt: fmt_exts.get(fmt, []) for fmt in list_formats()}
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    elif not ctx.obj.get("quiet"):
        for fmt in list_formats():
            exts = ", ".join(fmt_exts.get(fmt, []))
            out_console.print(f"  [bold]{fmt}[/bold]  {exts}")


if __name__ == "__main__":
    main()
