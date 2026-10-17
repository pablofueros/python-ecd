from pathlib import Path

import pytest

from python_ecd import utils


def write_solution(base_dir: Path, source: str, mode: str = "input") -> None:
    quest_dir = base_dir / "events/2025/quest_01"
    (quest_dir / mode).mkdir(parents=True)
    (quest_dir / "solution.py").write_text(source)
    (quest_dir / mode / f"{mode}_p1.txt").write_text("abc")


def test_find_base_walks_up_from_nested_directory(tmp_path, monkeypatch):
    nested = tmp_path / "events/2025/quest_01"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert utils.find_base() == tmp_path


def test_find_base_fails_outside_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match="run 'ecd init'"):
        utils.find_base()


def test_execute_part_loads_solution_and_data(tmp_path):
    write_solution(tmp_path, "def part_1(data):\n    return data.upper()\n")

    assert utils.execute_part(tmp_path, 1, 2025, 1) == "ABC"


def test_execute_part_rejects_missing_callable(tmp_path):
    write_solution(tmp_path, "part_1 = 'not callable'\n")

    with pytest.raises(TypeError, match="No callable 'part_1'"):
        utils.execute_part(tmp_path, 1, 2025, 1)


@pytest.mark.parametrize(
    ("milliseconds", "expected"),
    [
        (None, "?"),
        (0, "0s"),
        (1000, "1s"),
        (61_000, "1m 1s"),
        (90_061_000, "1d 1h 1m 1s"),
    ],
)
def test_format_duration(milliseconds, expected):
    assert utils.format_duration(milliseconds) == expected
