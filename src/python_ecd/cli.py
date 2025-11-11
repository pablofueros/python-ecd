from datetime import datetime
from typing import Literal

import typer

from . import utils
from .version import __version__

app = typer.Typer(name="python-ecd", help="python-ecd: CLI tool for Everybody Codes")


def _display_version(value: bool) -> None:
    """Display the version of the application and exit."""
    if value:
        typer.echo(f"python-ecd {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=_display_version,
        help="Display the version and exit.",
        is_eager=True,  # Process version before other logic
    ),
):
    pass


@app.command("init")
def init_cmd(
    path: str = typer.Argument(None, help="Path to initialize the workspace at"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """Initialize the workspace for Everybody Codes puzzles."""

    # 0. Parse inputs
    base_dir_name = "." if path is None else path
    token = typer.prompt("Session Token", default="", show_default=False)

    # 1. Create base directory
    base_dir = utils.create_base(base_dir_name)
    typer.echo(f"📁 Created workspace at: {base_dir}")

    # 2. Initialize git repository
    git_dir = base_dir / ".git"
    if not git_dir.exists():
        utils.create_git(base_dir)

    # 3. Create .gitignore
    gitignore_path = base_dir / ".gitignore"
    if gitignore_path.exists() and not force:
        typer.echo("⚠️ .gitignore already exists (use --force to overwrite).")
    else:
        utils.create_gitignore(base_dir)
        typer.echo("🛑 .gitignore created")

    # 4. Create README.md if requested
    readme_path = base_dir / "README.md"
    if readme_path.exists() and not force:
        typer.echo("⚠️ README.md already exists (use --force to overwrite).")
    else:
        utils.create_readme(base_dir, force)
        typer.echo("📝 README.md created")

    # 5. Save session token if provided
    token_path = utils.ENV_PATH
    if not token:
        typer.echo("⚠️ No session token provided (set it later with 'ecd set-token')")
    elif token_path.exists() and not force:
        typer.echo("⚠️ Session token file already exists (use --force to overwrite).")
    else:
        utils.set_token(token, force)
        typer.echo(f"🔑 Session token saved to {token_path}")


@app.command("set-token")
def set_token_cmd(
    token: str = typer.Argument(..., help="Session token to access puzzle inputs"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing token"),
) -> None:
    """Set the session token to operate with Everybody Codes webpage."""
    token_path = utils.ENV_PATH
    if token_path.exists() and not force:
        typer.echo("⚠️ Session token file already exists (use --force to overwrite).")
    else:
        utils.set_token(token, force)
        typer.echo(f"🔑 Session token saved to {token_path}")


@app.command("pull")
def pull_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int = typer.Option(datetime.now().year, "--year", "-y", help="Event year"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """Download available input data for a given quest and create local structure."""

    # 0. Locate base directory
    base_dir = utils.find_base()

    # 1. Ensure session token exists
    if not utils.get_token():
        typer.echo(
            "❌ Error: Session token not found in .env. Use 'ecd set-token' to set it."
        )
        raise typer.Exit(1)

    # 2. Download the available input
    try:
        input_dict = utils.download_input(year, quest)
    except Exception as e:
        typer.echo(f"❌ Failed to fetch input: {e}")
        raise typer.Exit(1)

    # 3. Prepare directory structure
    quest_dir = utils.create_quest_dir(base_dir, year, quest)

    # 4. Create solution.py if missing
    solution_file = quest_dir / "solution.py"
    if solution_file.exists() and not force:
        typer.echo(
            "⚠️ The solution python file already exists (use --force to overwrite)."
        )
    else:
        utils.create_solution(quest_dir, force)
        typer.echo("🧩 Created solution.py")

    for part, input in input_dict.items():
        # 5. Save available inputs
        input_file = quest_dir / f"input/input_p{part}.txt"
        if input_file.exists() and not force:
            typer.echo(
                f"⚠️ Input file for part {part} already exists (use --force to overwrite)."
            )
        else:
            input_file.write_text(input, encoding="utf-8")
            typer.echo(f"📥 Saved input for quest {quest:02d} part {part}.")

        # 6. Ensure empty test file exists
        test_file = quest_dir / f"test/test_p{part}.txt"
        if test_file.exists() and not force:
            typer.echo(
                f"⚠️ Test file for part {part} already exists (use --force to overwrite)."
            )
        else:
            test_file.touch(exist_ok=True)

    typer.echo(f"✅ Quest {quest:02d} ready at {solution_file.relative_to(base_dir)}")


@app.command("run")
def run_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int = typer.Option(datetime.now().year, "--year", "-y", help="Event year"),
    part: Literal[1, 2, 3] = typer.Option(
        1, "--part", "-p", help="Part number to execute"
    ),
) -> None:
    """Execute the solution for a given quest and part using input data."""

    # 0. Locate base directory
    base_dir = utils.find_base()

    # 1. Execute the solution
    try:
        result = utils.execute_part(base_dir, quest, year, part, mode="input")
    except Exception as e:
        typer.echo(f"❌ Failed to execute Quest {quest} Part {part}: {e}")
        raise typer.Exit(1)

    typer.echo(f"✅ Result for Quest {quest} Part {part}:\n{result}")


@app.command("test")
def test_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int = typer.Option(datetime.now().year, "--year", "-y", help="Event year"),
    part: Literal[1, 2, 3] = typer.Option(
        1, "--part", "-p", help="Part number to test"
    ),
) -> None:
    """Run the solution for a given quest and part using test data."""

    # 0. Locate base directory
    base_dir = utils.find_base()

    # 1. Execute the solution in test mode
    try:
        result = utils.execute_part(base_dir, quest, year, part, mode="test")
    except Exception as e:
        typer.echo(f"❌ Failed to run test for Quest {quest} Part {part}: {e}")
        raise typer.Exit(1)

    typer.echo(f"🧪 Test result for Quest {quest} Part {part}:\n{result}")


@app.command("push")
def push_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int = typer.Option(datetime.now().year, "--year", "-y", help="Event year"),
    part: Literal[1, 2, 3] = typer.Option(
        1, "--part", "-p", help="Part number to submit"
    ),
) -> None:
    """Submit the solution for a given quest and part."""

    # 0. Locate base directory
    base_dir = utils.find_base()

    # 1. Submit the solution
    try:
        result = utils.push_solution(base_dir, quest, year, part)
    except Exception as e:
        typer.echo(f"❌ Failed to submit solution for Quest {quest} Part {part}: {e}")
        raise typer.Exit(1)

    if result.get("correct"):
        typer.echo(
            f"✅ Correct answer for Quest {quest} Part {part}!"
            f"\n - Global place: {result.get('globalPlace', '?')}"
            f"\n - Global score: {result.get('globalScore', '?')}"
            f"\n - Global time: {utils.format_duration(result.get('globalTime'))}"
            f"\n - Local time: {utils.format_duration(result.get('localTime'))}"
        )

        # Download the next part (if the quest is not ended)
        if part == 3:
            return
        else:
            typer.echo()

        # Download the input for the given part
        try:
            input_dict = utils.download_input(year, quest)
        except Exception as e:
            typer.echo(f"❌ Failed to fetch input: {e}")
            raise typer.Exit(1)

        # Prepare directory structure
        quest_dir = utils.create_quest_dir(base_dir, year, quest)

        # 5. Save available inputs
        input_file = quest_dir / f"input/input_p{part + 1}.txt"
        if input_file.exists():
            typer.echo(
                f"⚠️ Input file for part {part + 1} already exists (use ecd pull --force to overwrite)."
            )
        else:
            input_file.write_text(input_dict[str(part + 1)], encoding="utf-8")
            typer.echo(f"📥 Saved input for quest {quest:02d} part {part + 1}.")

        # 6. Ensure empty test file exists
        test_file = quest_dir / f"test/test_p{part + 1}.txt"
        if test_file.exists():
            typer.echo(
                f"⚠️ Test file for part {part + 1} already exists (use ecd pull --force to overwrite)."
            )
        else:
            test_file.touch(exist_ok=True)

    else:
        typer.echo(
            f"❌ Incorrect answer for Quest {quest} Part {part}:"
            f"\n - lengthCorrect={result.get('lengthCorrect')}, "
            f"\n - firstCorrect={result.get('firstCorrect')}"
        )


if __name__ == "__main__":
    app()
