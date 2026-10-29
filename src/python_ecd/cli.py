import sys
from pathlib import Path
from typing import Literal

import typer

from . import utils
from .target import ChallengeTarget
from .version import __version__

app = typer.Typer(name="python-ecd", help="python-ecd: CLI tool for Everybody Codes")
token_app = typer.Typer(help="Manage Everybody Codes authentication.")
progress_app = typer.Typer(help="Show or synchronize accepted puzzle parts.")
app.add_typer(token_app, name="token")
app.add_typer(progress_app, name="progress")

TOTAL_QUESTS = {"events": 20, "stories": 3}


def _resolve_target(quest: int, year: int | None, story: int | None) -> ChallengeTarget:
    if (year is None) == (story is None):
        typer.echo("❌ Select exactly one target using --year or --story.")
        raise typer.Exit(2)
    if year is not None:
        return ChallengeTarget(category="event", edition=year, quest=quest)
    assert story is not None
    return ChallengeTarget(category="story", edition=story, quest=quest)


def _display_version(value: bool) -> None:
    """Display the version of the application and exit."""
    if value:
        typer.echo(f"python-ecd {__version__}")
        raise typer.Exit()


def _find_base() -> Path:
    try:
        return utils.find_base()
    except utils.WorkspaceMigrationRequired as error:
        typer.echo(f"⚠️ {error}")
        raise typer.Exit(1)
    except FileNotFoundError as error:
        typer.echo(f"❌ {error}")
        raise typer.Exit(1)


def _warn_legacy_env(base_dir: Path) -> None:
    if (base_dir / ".env").is_file():
        typer.echo("⚠️ Legacy .env detected. Run 'ecd token set', then delete .env.")


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
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
    no_git: bool = typer.Option(False, "--no-git", help="Do not initialize a Git repo"),
) -> None:
    """Initialize the workspace for Everybody Codes puzzles."""

    # 0. Parse inputs
    base_dir_name = "." if path is None else path

    # 1. Create or migrate the base directory
    base_dir = utils.create_base(base_dir_name)
    if utils.is_legacy_workspace(base_dir):
        utils.create_workspace_state(base_dir)
        typer.echo(f"🧭 {utils.WORKSPACE_FILE} created")
        _warn_legacy_env(base_dir)
        return

    state_existed = (base_dir / utils.WORKSPACE_FILE).exists()
    utils.create_workspace_state(base_dir)
    typer.echo(f"📁 Created workspace at: {base_dir}")
    if not state_existed:
        typer.echo(f"🧭 {utils.WORKSPACE_FILE} created")
    _warn_legacy_env(base_dir)

    # 2. Initialize git repository
    git_dir = base_dir / ".git"
    if not no_git and not git_dir.exists():
        utils.create_git(base_dir)

    # 3. Create .gitignore
    gitignore_path = base_dir / ".gitignore"
    if gitignore_path.exists() and not force:
        typer.echo("⚠️ .gitignore already exists (use --force to overwrite).")
    else:
        utils.create_gitignore(base_dir, force)
        typer.echo("🛑 .gitignore created")

    # 4. Create README.md if requested
    readme_path = base_dir / "README.md"
    if readme_path.exists() and not force:
        typer.echo("⚠️ README.md already exists (use --force to overwrite).")
    else:
        utils.create_readme(base_dir, force)
        typer.echo("📝 README.md created")


@token_app.command("set")
def token_set_cmd(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing token"),
) -> None:
    """Store the Everybody Codes session token."""
    token_path = utils.TOKEN_PATH
    if token_path.exists() and not force:
        typer.echo("⚠️ Session token file already exists (use --force to overwrite).")
    else:
        token = typer.prompt("Session Token", hide_input=True)
        utils.set_token(token, force)
        typer.echo(f"🔑 Session token saved to {token_path}")
        if utils.get_token_source() == "environment":
            typer.echo("⚠️ ECD_TOKEN is set and takes precedence over this file.")


@token_app.command("status")
def token_status_cmd() -> None:
    """Show the active token source without revealing the token."""
    source = utils.get_token_source()
    if source == "environment":
        typer.echo("🔑 Token configured from ECD_TOKEN.")
        if utils.TOKEN_PATH.is_file():
            typer.echo(f"ℹ️ Stored token at {utils.TOKEN_PATH} is currently overridden.")
        return
    if source == "file":
        typer.echo(f"🔑 Token configured from {utils.TOKEN_PATH}.")
        private = utils.token_file_is_private()
        if private is True:
            typer.echo("🔒 File permissions: private (0600).")
        elif private is False:
            typer.echo("⚠️ File permissions are not private (expected 0600).")
        return
    typer.echo("❌ Session token not found. Use 'ecd token set' or ECD_TOKEN.")
    raise typer.Exit(1)


@token_app.command("check")
def token_check_cmd() -> None:
    """Check the active token against Everybody Codes."""
    if not utils.has_token():
        typer.echo("❌ Session token not found. Use 'ecd token set' or ECD_TOKEN.")
        raise typer.Exit(1)
    try:
        utils.check_token()
    except Exception as e:
        typer.echo(f"❌ Token check failed: {e}")
        raise typer.Exit(1)
    typer.echo("✅ Token is valid.")


@token_app.command("remove")
def token_remove_cmd(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Remove the token stored in the config file."""
    token_path = utils.TOKEN_PATH
    if not token_path.is_file():
        typer.echo(f"ℹ️ No stored token found at {token_path}.")
        if utils.get_token_source() == "environment":
            typer.echo("⚠️ ECD_TOKEN remains configured in the environment.")
        return
    if not force and not typer.confirm(f"Remove the stored token at {token_path}?"):
        typer.echo("Token removal cancelled.")
        return
    utils.remove_token()
    typer.echo(f"🗑️ Removed stored token at {token_path}.")
    if utils.get_token_source() == "environment":
        typer.echo("⚠️ ECD_TOKEN remains configured in the environment.")


@app.command("pull")
def pull_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int | None = typer.Option(None, "--year", "-y", help="Event year"),
    story: int | None = typer.Option(None, "--story", "-s", help="Story number"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """Download available input data for a given quest and create local structure."""

    # 0. Resolve challenge and locate base directory
    target = _resolve_target(quest, year, story)
    base_dir = _find_base()

    # 1. Ensure session token exists
    if not utils.has_token():
        typer.echo("❌ Session token not found. Use 'ecd token set' or ECD_TOKEN.")
        raise typer.Exit(1)

    # 2. Download the available input
    try:
        input_dict = utils.download_input(target)
    except Exception as e:
        typer.echo(f"❌ Failed to fetch input: {e}")
        raise typer.Exit(1)

    # 3. Prepare directory structure
    quest_dir = utils.create_quest_dir(base_dir, target)

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
            typer.echo(f"📥 Saved input for {target.label} Part {part}.")

        # 6. Ensure empty test file exists
        test_file = quest_dir / f"test/test_p{part}.txt"
        if test_file.exists() and not force:
            typer.echo(
                f"⚠️ Test file for part {part} already exists (use --force to overwrite)."
            )
        else:
            test_file.touch(exist_ok=True)

    typer.echo(f"✅ {target.label} ready at {solution_file.relative_to(base_dir)}")


@app.command("run")
def run_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int | None = typer.Option(None, "--year", "-y", help="Event year"),
    story: int | None = typer.Option(None, "--story", "-s", help="Story number"),
    part: Literal[1, 2, 3] = typer.Option(
        1, "--part", "-p", help="Part number to execute"
    ),
) -> None:
    """Execute the solution for a given quest and part using input data."""

    # 0. Resolve challenge and locate base directory
    target = _resolve_target(quest, year, story)
    base_dir = _find_base()

    # 1. Execute the solution
    try:
        result = utils.execute_part(base_dir, target, part, mode="input")
    except Exception as e:
        typer.echo(f"❌ Failed to execute {target.label} Part {part}: {e}")
        raise typer.Exit(1)

    typer.echo(f"✅ Result for {target.label} Part {part}:\n{result}")


@app.command("test")
def test_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int | None = typer.Option(None, "--year", "-y", help="Event year"),
    story: int | None = typer.Option(None, "--story", "-s", help="Story number"),
    part: Literal[1, 2, 3] = typer.Option(
        1, "--part", "-p", help="Part number to test"
    ),
) -> None:
    """Run the solution for a given quest and part using test data."""

    # 0. Resolve challenge and locate base directory
    target = _resolve_target(quest, year, story)
    base_dir = _find_base()

    # 1. Execute the solution in test mode
    try:
        result = utils.execute_part(base_dir, target, part, mode="test")
    except Exception as e:
        typer.echo(f"❌ Failed to run test for {target.label} Part {part}: {e}")
        raise typer.Exit(1)

    typer.echo(f"🧪 Test result for {target.label} Part {part}:\n{result}")


@app.command("push")
def push_cmd(
    quest: int = typer.Argument(..., help="Quest number (e.g. 3)"),
    year: int | None = typer.Option(None, "--year", "-y", help="Event year"),
    story: int | None = typer.Option(None, "--story", "-s", help="Story number"),
    part: Literal[1, 2, 3] = typer.Option(
        1, "--part", "-p", help="Part number to submit"
    ),
) -> None:
    """Submit the solution for a given quest and part."""

    # 0. Resolve challenge and locate base directory
    target = _resolve_target(quest, year, story)
    base_dir = _find_base()

    # Ensure session token exists
    if not utils.has_token():
        typer.echo("❌ Session token not found. Use 'ecd token set' or ECD_TOKEN.")
        raise typer.Exit(1)

    # 1. Submit the solution
    try:
        result = utils.push_solution(base_dir, target, part)
    except Exception as e:
        typer.echo(f"❌ Failed to submit solution for {target.label} Part {part}: {e}")
        raise typer.Exit(1)

    if result.get("correct"):
        try:
            utils.record_completed_part(base_dir, target, part)
        except Exception as e:
            typer.echo(f"❌ Answer accepted, but progress could not be saved: {e}")
            raise typer.Exit(1)
        typer.echo(
            f"✅ Correct answer for {target.label} Part {part}!"
            f"\n- Global place: {result.get('globalPlace', '?')}"
            f"\n- Global score: {result.get('globalScore', '?')}"
            f"\n- Global time: {utils.format_duration(result.get('globalTime'))}"
            f"\n- Local time: {utils.format_duration(result.get('localTime'))}"
        )

        # Download the next part (if the quest is not ended)
        if part == 3:
            return
        else:
            typer.echo()

        # Download the input for the given part
        try:
            input_dict = utils.download_input(target)
        except Exception as e:
            typer.echo(f"❌ Failed to fetch input: {e}")
            raise typer.Exit(1)

        # Prepare directory structure
        quest_dir = utils.create_quest_dir(base_dir, target)

        # 5. Save available inputs
        input_file = quest_dir / f"input/input_p{part + 1}.txt"
        if input_file.exists():
            typer.echo(
                f"⚠️ Input file for part {part + 1} already exists (use ecd pull --force to overwrite)."
            )
        else:
            input_file.write_text(input_dict[str(part + 1)], encoding="utf-8")
            typer.echo(f"📥 Saved input for {target.label} Part {part + 1}.")

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
            f"❌ Incorrect answer for {target.label} Part {part}:"
            f"\n- lengthCorrect={result.get('lengthCorrect')}"
            f"\n- firstCorrect={result.get('firstCorrect')}"
        )


def _display_progress(progress: utils.Progress, targets: list[ChallengeTarget]) -> None:
    known_quests: dict[str, dict[int, set[int]]] = {"events": {}, "stories": {}}
    for collection in ("events", "stories"):
        for edition, quests in progress[collection].items():
            known_quests[collection][edition] = set(quests)
    for target in targets:
        collection = "events" if target.category == "event" else "stories"
        known_quests[collection].setdefault(target.edition, set()).add(target.quest)

    if not any(known_quests.values()):
        typer.echo("ℹ️ No completed parts recorded yet.")
        return

    for collection, heading in (("events", "Events"), ("stories", "Stories")):
        if not known_quests[collection]:
            continue
        typer.echo(heading)
        for edition, quest_numbers in sorted(known_quests[collection].items()):
            recorded = progress[collection].get(edition, {})
            completed_quests = sum(
                recorded.get(quest) == [1, 2, 3] for quest in quest_numbers
            )
            completed_parts = sum(
                len(recorded.get(quest, [])) for quest in quest_numbers
            )
            total_quests = TOTAL_QUESTS[collection]
            total_parts = total_quests * 3
            typer.echo(
                f"  {edition}: {completed_quests}/{total_quests} quests complete, "
                f"{completed_parts}/{total_parts} parts complete"
            )


@progress_app.callback(invoke_without_command=True)
def progress_cmd(ctx: typer.Context) -> None:
    """Show accepted parts recorded in the workspace."""
    if ctx.invoked_subcommand is not None:
        return
    base_dir = _find_base()
    try:
        progress = utils.load_progress(base_dir)
    except Exception as e:
        typer.echo(f"❌ Failed to read progress: {e}")
        raise typer.Exit(1)
    _display_progress(progress, utils.discover_targets(base_dir))


@progress_app.command("sync")
def progress_sync_cmd() -> None:
    """Synchronize progress for quests present in the workspace."""
    base_dir = _find_base()
    if not utils.has_token():
        typer.echo("❌ Session token not found. Use 'ecd token set' or ECD_TOKEN.")
        raise typer.Exit(1)

    targets = utils.discover_targets(base_dir)
    if not targets:
        typer.echo("ℹ️ No local quests found to synchronize.")
        return

    try:
        updates = []
        try:
            with typer.progressbar(
                targets, label="Synchronizing progress", show_pos=True
            ) as progress:
                for target in progress:
                    updates.append((target, utils.fetch_completed_parts(target)))
        finally:
            if sys.stdout.isatty():
                typer.echo("\033[1A\033[2K\r", nl=False)
        progress = utils.load_progress(base_dir)
        for target, parts in updates:
            collection = "events" if target.category == "event" else "stories"
            editions = progress[collection]
            quests = editions.setdefault(target.edition, {})
            if parts:
                quests[target.quest] = parts
            else:
                quests.pop(target.quest, None)
            if not quests:
                editions.pop(target.edition)
        utils.save_progress(base_dir, progress)
    except Exception as e:
        typer.echo(f"❌ Failed to synchronize progress: {e}")
        raise typer.Exit(1)

    typer.echo(f"✅ Synchronized progress for {len(targets)} quests.")
    _display_progress(progress, targets)


if __name__ == "__main__":
    app()
