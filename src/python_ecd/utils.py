import contextlib
import importlib.util
import io
import os
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv, set_key
from ecd import get_inputs, submit


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
    Create the base directory for the project, including subfolders.
    """
    base_dir = Path(base_dir_name).resolve()
    (base_dir / "events").mkdir(parents=True, exist_ok=True)
    return base_dir


def find_base() -> Path:
    """
    Locate the base directory by searching upwards from the current directory.
    """
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / "events").exists():
            return parent
    raise FileNotFoundError("Base directory not found. Please run 'ecd init'.")


def create_quest_dir(base_dir: Path, year: int, quest: int) -> Path:
    """
    Create directory structure for a given quest/year.
    """
    quest_dir = base_dir / "events" / str(year) / f"quest_{quest:02d}"
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


def create_gitignore(base_dir: Path) -> None:
    gitignore_path = base_dir / ".gitignore"
    if not gitignore_path.exists():
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


ENV_PATH = Path(".env")


def set_token(token: str, force: bool = False) -> None:
    """Store the session token in the .env file."""
    ENV_PATH.touch(exist_ok=True)
    load_dotenv(dotenv_path=ENV_PATH)
    set_key(str(ENV_PATH), "ECD_TOKEN", token.strip())


def get_token() -> str | None:
    """Return the session token from the .env file, or None if not found."""
    load_dotenv(dotenv_path=ENV_PATH)
    return os.getenv("ECD_TOKEN")


def download_input(year: int, quest: int) -> dict[str, str]:
    """
    Fetch the available input text for a specific quest.
    """
    with contextlib.redirect_stderr(io.StringIO()):
        return get_inputs(quest=quest, event=year)


def execute_part(
    base_dir: Path,
    quest: int,
    year: int,
    part: Literal[1, 2, 3],
    mode: str = "input",
) -> str:
    """
    Execute a given part of a quest solution with either input or test data.

    Args:
        base_dir: Base directory
        part: Part number (1, 2, or 3)
        mode: Either "input" or "test"

    Returns:
        The string result produced by part_{part}(data).
    """

    quest_dir = base_dir / "events" / str(year) / f"quest_{quest:02d}"
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
        raise AttributeError(f"No function '{func_name}' defined in solution.py")

    # Run the function
    result = func(data)
    if result is None:
        raise ValueError(f"{func_name} returned None.")

    return str(result)


def push_solution(
    base_dir: Path,
    quest: int,
    year: int,
    part: Literal[1, 2, 3],
) -> dict:
    """
    Submit the solution for a given quest and part using input data.

    Returns:
        The response message from the submission.
    """

    quest_dir = base_dir / "events" / str(year) / f"quest_{quest:02d}"
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
        raise AttributeError(f"No function '{func_name}' defined in solution.py")

    # Fetch input data
    input_dict = download_input(year=year, quest=quest)
    input_text = input_dict[str(part)]

    # Run the function
    answer = func(input_text)
    if answer is None:
        raise ValueError(f"{func_name} returned None.")

    # Submit the answer
    with contextlib.redirect_stderr(io.StringIO()):
        result = submit(
            quest=quest,
            event=year,
            part=part,
            answer=str(answer),
            quiet=True,
        )

    if result.status != 200:
        raise RuntimeError(f"Submission failed with status {result.status}")

    return result.json()


def format_duration(ms: int | float | None) -> str:
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
