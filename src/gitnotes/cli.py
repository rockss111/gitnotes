import json
import shutil
from pathlib import Path

import click
from click.exceptions import Exit as ClickExit
from .config_resolver import resolve_editor, ConfigNotResolvedError
from .export import export_note
from .init_cmd import init_repository, InitializationError
from .search import search_notes
from .session import Session, EditResult


@click.group()
def main():
    pass


def _edit_session(name: str, editor: str | None = None) -> None:
    try:
        editor_cmd = resolve_editor() if editor is None else editor
    except ConfigNotResolvedError:
        raise ClickExit(code=1)

    try:
        with Session(name, Path.cwd()) as session:
            result = session.edit(editor_cmd)

            if result == EditResult.CHANGED:
                click.echo(session.diff())
                if click.confirm("Accept changes?"):
                    session.commit()
                else:
                    session.restore()
            elif result == EditResult.EMPTY:
                if not click.confirm("Note is empty. Keep?"):
                    session.restore()
                    raise ClickExit(code=1)
            elif result == EditResult.DELETED:
                click.echo("Note was deleted. Restoring.")
                session.restore()
                raise ClickExit(code=1)
            elif result == EditResult.INVALID:
                click.echo("Invalid UTF-8 content. Restoring.")
                session.restore()
                raise ClickExit(code=1)
    except OSError:
        raise ClickExit(code=1)


@main.command()
def init():
    if not shutil.which("git"):
        raise ClickExit(code=2)
    try:
        init_repository()
    except InitializationError:
        raise ClickExit(code=1)


@main.command()
@click.argument("name")
@click.option("--editor", default=None)
def new(name, editor):
    if not name.endswith(".md"):
        name = f"{name}.md"

    Path.cwd().joinpath(name).write_text("")
    _edit_session(name, editor)


@main.command()
@click.argument("name")
@click.option("--editor", default=None)
def edit(name, editor):
    if not name.endswith(".md"):
        name = f"{name}.md"

    if not Path.cwd().joinpath(name).is_file():
        raise ClickExit(code=1)

    _edit_session(name, editor)


@main.command()
@click.argument("query")
@click.option("--context", default=3, type=int, help="Lines of context")
@click.option("--json", "json_output", is_flag=True, default=False)
def search(query, context, json_output):
    result = search_notes(query)

    if json_output:
        click.echo(
            json.dumps(
                [
                    {
                        "file": m.file,
                        "line": m.line,
                        "content": m.content,
                        "context_before": list(m.context_before),
                        "context_after": list(m.context_after),
                    }
                    for m in result.matches
                ]
            )
        )
    else:
        click.echo(result.raw, nl=False)

    raise ClickExit(code=result.exit_code)


@main.command()
@click.argument("name")
@click.option("--format", default="html")
def export(name, format):
    if not name.endswith(".md"):
        name = f"{name}.md"

    note_path = Path.cwd() / name
    if not note_path.is_file():
        raise ClickExit(code=1)

    result = export_note(note_path)

    if not result.success:
        if result.exit_code is None:
            raise ClickExit(code=2)
        raise ClickExit(code=1)
