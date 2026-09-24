"""Command line entry point: `lfe check` and `lfe fix`."""

from __future__ import annotations

import click

from . import __version__


@click.group()
@click.version_option(__version__, prog_name="lfe")
def main() -> None:
    """Analyse and normalise legal .docx files."""


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def check(path: str) -> None:
    """Score PATH 0-100 and report findings. (M1)"""
    raise click.ClickException("not implemented yet: see milestone M1")


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--style", required=True, type=click.Path(exists=True, dir_okay=False),
              help="House style: a reference .docx or a style JSON file.")
def fix(path: str, style: str) -> None:
    """Normalise PATH against a house style. (M3)"""
    raise click.ClickException("not implemented yet: see milestone M3")
