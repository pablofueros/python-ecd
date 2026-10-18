import contextlib
import importlib.util
import io
import os
import stat
import subprocess
import tempfile
import tomllib
import urllib.request
from datetime import timedelta
from pathlib import Path
from typing import Literal

from .target import ChallengeTarget

WORKSPACE_FILE = ".ecd.toml"
WORKSPACE_SCHEMA_VERSION = 1


class WorkspaceMigrationRequired(FileNotFoundError):
    """Raised when a legacy workspace needs an .ecd.toml file."""


def _read_template(template_name: str) -> str:
    """
    Read a template file from the templates directory.
    """
    templates_dir = Path(__file__).parent / "templates"
    template_path = templates_dir / template_name
    text = template_path.read_text(encoding="utf-8")
    return text


def create_base(base_dir_name: str) -> Path:
    """
    Create the base directory for the project.
    """
    base_dir = Path(base_dir_name).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def is_legacy_workspace(base_dir: Path) -> bool:
    """Return whether a directory looks like a workspace without its state file."""
    return not (base_dir / WORKSPACE_FILE).is_file() and (
        (base_dir / "events").is_dir() or (base_dir / "stories").is_dir()
    )


def create_workspace_state(base_dir: Path) -> Path:
    """Create an empty workspace state file without replacing existing progress."""
    state_path = base_dir / WORKSPACE_FILE
    if not state_path.exists():
        state_path.write_text(
            f"schema_version = {WORKSPACE_SCHEMA_VERSION}\n", encoding="utf-8"
        )
    return state_path


def find_base() -> Path:
    """
    Locate the base directory by searching upwards from the current directory.
    """
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / WORKSPACE_FILE).is_file():
            return parent
        if is_legacy_workspace(parent):
            raise WorkspaceMigrationRequired(
                "Legacy workspace detected: .ecd.toml is missing. "
                "Run 'ecd init' from the workspace root to migrate it."
            )
    raise FileNotFoundError("Base directory not found. Please run 'ecd init'.")


def load_progress(base_dir: Path) -> dict[str, dict[int, dict[int, list[int]]]]:
    """Load completed parts grouped by category, edition, and quest."""
    state_path = base_dir / WORKSPACE_FILE
    with state_path.open("rb") as state_file:
        state = tomllib.load(state_file)
    if state.get("schema_version") != WORKSPACE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported workspace schema in {WORKSPACE_FILE}: "
            f"{state.get('schema_version')!r}"
        )

    progress: dict[str, dict[int, dict[int, list[int]]]] = {
        "events": {},
        "stories": {},
    }
    for collection, editions in progress.items():
        raw_editions = state.get(collection, {})
        if not isinstance(raw_editions, dict):
            raise TypeError(f"Invalid [{collection}] data in {WORKSPACE_FILE}.")
        for edition_key, raw_quests in raw_editions.items():
            if not isinstance(raw_quests, dict):
                raise TypeError(f"Invalid {collection}.{edition_key} data.")
            edition = int(edition_key)
            quests: dict[int, list[int]] = {}
            for quest_key, raw_parts in raw_quests.items():
                if not quest_key.startswith("quest_") or not isinstance(
                    raw_parts, list
                ):
                    raise ValueError(f"Invalid progress entry: {quest_key}.")
                quest = int(quest_key.removeprefix("quest_"))
                parts = sorted({int(part) for part in raw_parts})
                if any(part not in (1, 2, 3) for part in parts):
                    raise ValueError(f"Invalid completed part in {quest_key}.")
                quests[quest] = parts
            editions[edition] = quests
    return progress


def _serialize_progress(
    progress: dict[str, dict[int, dict[int, list[int]]]],
) -> str:
    lines = [f"schema_version = {WORKSPACE_SCHEMA_VERSION}"]
    for collection in ("events", "stories"):
        for edition in sorted(progress[collection]):
            lines.extend(("", f'[{collection}."{edition}"]'))
            for quest in sorted(progress[collection][edition]):
                parts = sorted(set(progress[collection][edition][quest]))
                values = ", ".join(str(part) for part in parts)
                lines.append(f"quest_{quest:02d} = [{values}]")
    return "\n".join(lines) + "\n"


def record_completed_part(
    base_dir: Path, target: ChallengeTarget, part: Literal[1, 2, 3]
) -> None:
    """Record an accepted part and atomically update the workspace state."""
    progress = load_progress(base_dir)
    collection = "events" if target.category == "event" else "stories"
    quests = progress[collection].setdefault(target.edition, {})
    completed_parts = quests.setdefault(target.quest, [])
    completed_parts.append(part)

    state_path = base_dir / WORKSPACE_FILE
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=base_dir, prefix=".ecd.", delete=False
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        temporary_file.write(_serialize_progress(progress))
    temporary_path.replace(state_path)


def create_quest_dir(base_dir: Path, target: ChallengeTarget) -> Path:
    """
    Create the directory structure for an event or story quest.
    """
    quest_dir = base_dir / target.relative_dir
    quest_dir.mkdir(parents=True, exist_ok=True)
    (quest_dir / "input").mkdir(exist_ok=True)
    (quest_dir / "test").mkdir(exist_ok=True)
    return quest_dir


def create_readme(base_dir: Path, force: bool) -> None:
    """
    Create a simple README.md in the base directory.
    """
    readme_path = base_dir / "README.md"
    if not readme_path.exists() or force:
        content = _read_template("README.md.tpl")
        readme_path.write_text(content, encoding="utf-8")


def create_git(base_dir: Path) -> None:
    """
    Initialize a git repository in the base directory.
    """
    git_dir = base_dir / ".git"
    if git_dir.exists():
        return  # Git already initialized
    subprocess.run(
        ["git", "init"],
        cwd=str(base_dir),
        check=True,
        stdout=subprocess.DEVNULL,
    )


def create_gitignore(base_dir: Path, force: bool = False) -> None:
    gitignore_path = base_dir / ".gitignore"
    if not gitignore_path.exists() or force:
        content = _read_template(".gitignore.tpl")
        gitignore_path.write_text(content, encoding="utf-8")


def create_solution(quest_dir: Path, force: bool) -> None:
    """
    Create a solution.py file in the quest directory.
    """
    solution_path = quest_dir / "solution.py"
    if not solution_path.exists() or force:
        content = _read_template("solution.py.tpl")
        solution_path.write_text(content, encoding="utf-8")


TOKEN_PATH = Path("~/.config/ecd/token").expanduser()
TOKEN_CHECK_URL = "https://api.everybody.codes/user/me"

type TokenSource = Literal["environment", "file"]


def set_token(token: str, force: bool = False, token_path: Path | None = None) -> Path:
    """Store the session token in the global Everybody Codes config file."""
    path = TOKEN_PATH if token_path is None else token_path
    value = token.strip()
    if not value:
        raise ValueError("Session token cannot be empty.")
    if path.exists() and not force:
        raise FileExistsError(f"Session token file already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{value}\n", encoding="utf-8")
    if os.name != "nt":
        path.parent.chmod(0o700)
        path.chmod(0o600)
    return path


def get_token() -> str:
    """Read the active token, preferring the environment over the config file."""
    environment_token = os.getenv("ECD_TOKEN", "").strip()
    if environment_token:
        return environment_token
    if TOKEN_PATH.is_file():
        values = TOKEN_PATH.read_text(encoding="utf-8").split()
        if values:
            return values[0]
    raise ValueError("Session token not found.")


def get_token_source() -> TokenSource | None:
    """Return where the active token comes from without exposing its value."""
    if os.getenv("ECD_TOKEN", "").strip():
        return "environment"
    if TOKEN_PATH.is_file() and TOKEN_PATH.read_text(encoding="utf-8").split():
        return "file"
    return None


def has_token() -> bool:
    """Return whether auth is available from the environment or config file."""
    return get_token_source() is not None


def token_file_is_private() -> bool | None:
    """Check POSIX token permissions, or return None when not applicable."""
    if os.name == "nt" or not TOKEN_PATH.is_file():
        return None
    return stat.S_IMODE(TOKEN_PATH.stat().st_mode) == 0o600


def check_token() -> None:
    """Validate the active token against the Everybody Codes profile endpoint."""
    token = get_token()
    request = urllib.request.Request(
        TOKEN_CHECK_URL,
        headers={
            "Cookie": f"everybody-codes={token}",
            "User-Agent": "python-ecd",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"Everybody Codes returned HTTP {response.status}.")


def remove_token() -> bool:
    """Remove the stored token file and report whether one existed."""
    if not TOKEN_PATH.is_file():
        return False
    TOKEN_PATH.unlink()
    return True


def download_input(target: ChallengeTarget) -> dict[str, str]:
    """
    Fetch the available input text for a specific quest.
    """
    from ecd import get_inputs

    return get_inputs(quest=target.quest, event=target.api_event)


def execute_part(
    base_dir: Path,
    target: ChallengeTarget,
    part: Literal[1, 2, 3],
    mode: str = "input",
) -> str:
    """
    Execute a given part of a quest solution with either input or test data.

    Args:
        base_dir: Base directory
        target: Event or story quest to execute
        part: Part number (1, 2, or 3)
        mode: Either "input" or "test"

    Returns:
        The string result produced by part_{part}(data).
    """

    quest_dir = base_dir / target.relative_dir
    solution_path = quest_dir / "solution.py"
    data_path = quest_dir / mode / f"{mode}_p{part}.txt"

    if not solution_path.exists():
        raise FileNotFoundError(
            f"Missing solution file: {solution_path.relative_to(base_dir)}"
        )
    if not data_path.exists():
        raise FileNotFoundError(f"Missing data file: {data_path.relative_to(base_dir)}")

    # Load data
    data = data_path.read_text(encoding="utf-8")

    # Dynamic import
    spec = importlib.util.spec_from_file_location("solution", solution_path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load module from {solution_path.relative_to(base_dir)}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func_name = f"part_{part}"
    func = getattr(module, func_name, None)
    if not callable(func):
        raise TypeError(f"No callable '{func_name}' defined in solution.py")

    # Run the function
    result = func(data)
    if result is None:
        raise ValueError(f"{func_name} returned None.")

    return str(result)


def push_solution(
    base_dir: Path,
    target: ChallengeTarget,
    part: Literal[1, 2, 3],
) -> dict:
    """
    Submit the solution for a given quest and part using input data.

    Returns:
        The response message from the submission.
    """
    from ecd import submit

    quest_dir = base_dir / target.relative_dir
    solution_path = quest_dir / "solution.py"
    if not solution_path.exists():
        raise FileNotFoundError(
            f"Missing solution file: {solution_path.relative_to(base_dir)}"
        )

    # Dynamic import
    spec = importlib.util.spec_from_file_location("solution", solution_path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load module from {solution_path.relative_to(base_dir)}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func_name = f"part_{part}"
    func = getattr(module, func_name, None)
    if not callable(func):
        raise TypeError(f"No callable '{func_name}' defined in solution.py")

    # Fetch input data
    input_dict = download_input(target)
    input_text = input_dict[str(part)]

    # Run the function without leaking solution debug output into push output
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        answer = func(input_text)
    if answer is None:
        raise ValueError(f"{func_name} returned None.")

    # Submit the answer
    result = submit(
        quest=target.quest,
        event=target.api_event,
        part=part,
        answer=str(answer),
        quiet=True,
    )

    if result.status != 200:
        raise RuntimeError(f"Submission failed with status {result.status}")

    return result.json()


def format_duration(ms: float | None) -> str:
    """Format duration in milliseconds to a human-readable string using timedelta."""
    if ms is None:
        return "?"

    td = timedelta(milliseconds=ms)

    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)
