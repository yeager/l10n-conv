"""CLI entry point for l10n-conv."""

from __future__ import annotations

import os
import sys

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .model import TranslationCatalog, EntryState
from .registry import detect_format, get_format, list_formats

console = Console(stderr=True)
out_console = Console()


def _read_catalog(filepath: str, fmt: str | None = None) -> tuple[TranslationCatalog, str]:
    """Read a catalog, auto-detecting format if needed."""
    if filepath == "-":
        if not fmt:
            raise click.UsageError("Format must be specified when reading from stdin (-f/--format)")
        handler = get_format(fmt)()
        return handler.read_stdin(), fmt

    if not fmt:
        fmt = detect_format(filepath)
        if not fmt:
            raise click.UsageError(f"Cannot detect format of {filepath}. Use -f/--format.")
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
                    console.print(f"[yellow]⚠ Skipping {fpath}: {e}[/yellow]")


def _show_about(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"l10n-conv {__version__}")
    click.echo("Universal localization file converter, validator, and compiler")
    click.echo()
    click.echo("Author:     Daniel Nylander <daniel@danielnylander.se>")
    click.echo("License:    GPL-3.0-or-later")
    click.echo("Website:    https://github.com/yeager/l10n-conv")
    click.echo("PyPI:       https://pypi.org/project/l10n-conv/")
    click.echo("Translate:  https://app.transifex.com/danielnylander/l10n-conv/")
    ctx.exit()


@click.group()
@click.version_option(__version__, prog_name="l10n-conv")
@click.option("--about", is_flag=True, callback=_show_about, expose_value=False, is_eager=True, help="Show application info and exit")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.pass_context
def main(ctx, verbose):
    """l10n-conv — Universal localization file converter, validator, and compiler."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command()
@click.argument("input", type=str)
@click.option("-f", "--format", "in_fmt", help="Input format")
@click.option("--to", "out_fmt", help="Output format")
@click.option("-o", "--output", help="Output file (- for stdout)")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
@click.option("--batch", is_flag=True, help="Process directory recursively")
@click.pass_context
def convert(ctx, input, in_fmt, out_fmt, output, dry_run, batch):
    """Convert between localization formats."""
    if not out_fmt and not output:
        raise click.UsageError("Specify --to <format> or -o <output>")

    if not out_fmt and output and output != "-":
        out_fmt = detect_format(output)
        if not out_fmt:
            raise click.UsageError(f"Cannot detect output format from {output}. Use --to.")

    if batch:
        def _conv(fpath, **kw):
            catalog, _ = _read_catalog(fpath, in_fmt)
            if output:
                rel = os.path.relpath(fpath, input)
                base = os.path.splitext(rel)[0]
                ext_map = {f: e for e, f in _get_ext_map().items()}
                ext = ext_map.get(out_fmt, ".out")
                opath = os.path.join(output, base + ext)
            else:
                opath = "-"
            if dry_run:
                console.print(f"[dim]Would convert {fpath} → {opath}[/dim]")
                return
            _write_catalog(catalog, opath, out_fmt)
            if ctx.obj.get("verbose"):
                console.print(f"[green]✓[/green] {fpath} → {opath}")

        _process_batch(input, _conv)
        return

    catalog, detected = _read_catalog(input, in_fmt)
    if dry_run:
        console.print(f"[dim]Would convert {input} ({detected}) → {output or 'stdout'} ({out_fmt})[/dim]")
        console.print(f"[dim]{len(catalog.entries)} entries[/dim]")
        return

    _write_catalog(catalog, output or "-", out_fmt)
    if ctx.obj.get("verbose"):
        console.print(f"[green]✓[/green] Converted {len(catalog.entries)} entries from {detected} to {out_fmt}")


def _get_ext_map():
    from .registry import _EXT_MAP
    return _EXT_MAP


@main.command()
@click.argument("input", type=str)
@click.option("-o", "--output", required=True, help="Output file")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def compile(ctx, input, output, dry_run):
    """Compile localization files (.po→.mo, .ts→.qm)."""
    fmt = detect_format(input)
    if fmt == "po":
        if dry_run:
            console.print(f"[dim]Would compile {input} → {output} (PO→MO)[/dim]")
            return
        catalog, _ = _read_catalog(input, "po")
        _write_catalog(catalog, output, "mo")
        console.print(f"[green]✓[/green] Compiled {input} → {output}")
    elif fmt == "qt-ts":
        if dry_run:
            console.print(f"[dim]Would compile {input} → {output} (TS→QM)[/dim]")
            return
        # Qt QM compilation - use lrelease if available, else warn
        import subprocess
        try:
            subprocess.run(["lrelease", input, "-qm", output], check=True, capture_output=True)
            console.print(f"[green]✓[/green] Compiled {input} → {output}")
        except FileNotFoundError:
            console.print("[red]✗ lrelease not found. Install Qt tools for .ts→.qm compilation.[/red]")
            sys.exit(1)
    else:
        console.print(f"[red]✗ Compilation not supported for format: {fmt}[/red]")
        sys.exit(1)


@main.command()
@click.argument("source_dir", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output file")
@click.option("-f", "--format", "out_fmt", default="po", help="Output format (default: po)")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def extract(ctx, source_dir, output, out_fmt, dry_run):
    """Extract translatable strings from source code."""
    from .extractor import extract_from_directory

    catalog = extract_from_directory(source_dir)

    if dry_run:
        console.print(f"[dim]Would extract {len(catalog.entries)} strings → {output}[/dim]")
        return

    _write_catalog(catalog, output, out_fmt)
    console.print(f"[green]✓[/green] Extracted {len(catalog.entries)} strings → {output}")


@main.command()
@click.argument("file", type=str)
@click.option("-f", "--format", "fmt", help="File format")
@click.pass_context
def check(ctx, file, fmt):
    """Validate a localization file."""
    from .checker import check_catalog

    catalog, detected = _read_catalog(file, fmt)
    results = check_catalog(catalog)

    if not results:
        console.print(f"[green]✓[/green] {file}: No issues found")
        sys.exit(0)

    errors = warnings = infos = 0
    for r in results:
        icon = {"error": "[red]✗[/red]", "warning": "[yellow]⚠[/yellow]", "info": "[blue]ℹ[/blue]"}
        console.print(f"  {icon.get(r.level, '?')} {r.message}: {r.key}" +
                       (f" ({r.details})" if r.details else ""))
        if r.level == "error":
            errors += 1
        elif r.level == "warning":
            warnings += 1
        else:
            infos += 1

    console.print(f"\n{errors} errors, {warnings} warnings, {infos} info")
    sys.exit(1 if errors else (2 if warnings else 0))


@main.command()
@click.argument("file", type=str)
@click.option("-f", "--format", "fmt", help="File format")
@click.pass_context
def stats(ctx, file, fmt):
    """Show translation statistics."""
    catalog, detected = _read_catalog(file, fmt)

    table = Table(title=f"Statistics: {file}")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    total = len(catalog.entries)
    table.add_row("Total entries", str(total))
    table.add_row("Translated", f"[green]{catalog.translated_count}[/green]")
    table.add_row("Untranslated", f"[red]{catalog.untranslated_count}[/red]")
    table.add_row("Fuzzy", f"[yellow]{catalog.fuzzy_count}[/yellow]")
    table.add_row("Completion", f"{catalog.completion_percent}%")
    if catalog.target_language:
        table.add_row("Language", catalog.target_language)

    out_console.print(table)


@main.command()
@click.argument("base", type=str)
@click.argument("update", type=str)
@click.option("-o", "--output", required=True, help="Output file")
@click.option("-f", "--format", "fmt", help="File format")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def merge(ctx, base, update, output, fmt, dry_run):
    """Merge two localization files (like msgmerge)."""
    base_cat, detected = _read_catalog(base, fmt)
    update_cat, _ = _read_catalog(update, fmt or detected)

    # Merge: take base as template, update translations from update
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
        console.print(f"[dim]Would merge {merged} translations from {update} into {base}[/dim]")
        return

    _write_catalog(base_cat, output, fmt or detected)
    console.print(f"[green]✓[/green] Merged {merged} translations → {output}")


@main.command()
@click.argument("file1", type=str)
@click.argument("file2", type=str)
@click.option("-f", "--format", "fmt", help="File format")
@click.pass_context
def diff(ctx, file1, file2, fmt):
    """Show differences between two localization files."""
    cat1, detected = _read_catalog(file1, fmt)
    cat2, _ = _read_catalog(file2, fmt or detected)

    map1 = {(e.key, e.context): e for e in cat1.entries}
    map2 = {(e.key, e.context): e for e in cat2.entries}

    all_keys = sorted(set(map1.keys()) | set(map2.keys()))

    added = removed = changed = 0
    for key in all_keys:
        e1 = map1.get(key)
        e2 = map2.get(key)

        if e1 and not e2:
            console.print(f"[red]- {key[0]}[/red]: {e1.target}")
            removed += 1
        elif e2 and not e1:
            console.print(f"[green]+ {key[0]}[/green]: {e2.target}")
            added += 1
        elif e1.target != e2.target:
            console.print(f"[yellow]~ {key[0]}[/yellow]:")
            console.print(f"  [red]- {e1.target}[/red]")
            console.print(f"  [green]+ {e2.target}[/green]")
            changed += 1

    console.print(f"\n{added} added, {removed} removed, {changed} changed")


@main.command()
@click.argument("template", type=str)
@click.option("-l", "--lang", required=True, help="Target language code")
@click.option("-o", "--output", required=True, help="Output file")
@click.option("-f", "--format", "fmt", help="File format")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def init(ctx, template, lang, output, fmt, dry_run):
    """Create a new language file from a template."""
    catalog, detected = _read_catalog(template, fmt)
    catalog.target_language = lang

    # Clear all translations
    for entry in catalog.entries:
        entry.target = ""
        entry.state = EntryState.UNTRANSLATED
        entry.plural_targets = {}

    if dry_run:
        console.print(f"[dim]Would create {output} for language {lang} with {len(catalog.entries)} entries[/dim]")
        return

    _write_catalog(catalog, output, fmt or detected)
    console.print(f"[green]✓[/green] Created {output} for language '{lang}' with {len(catalog.entries)} entries")


@main.command(name="formats")
def list_formats_cmd():
    """List all supported formats."""
    table = Table(title="Supported Formats")
    table.add_column("Format", style="bold")
    table.add_column("Extensions")

    from .registry import _EXT_MAP
    fmt_exts: dict[str, list[str]] = {}
    for ext, fmt in _EXT_MAP.items():
        fmt_exts.setdefault(fmt, []).append(ext)

    for fmt in list_formats():
        exts = ", ".join(fmt_exts.get(fmt, []))
        out_console.print(f"  [bold]{fmt}[/bold]  {exts}")


if __name__ == "__main__":
    main()
