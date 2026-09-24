"""The CLI wiring is real even while the commands are stubs."""

from click.testing import CliRunner

from lfe import __version__
from lfe.cli import main


def test_version_is_reported() -> None:
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_check_and_fix_are_registered() -> None:
    assert set(main.commands) == {"check", "fix"}
