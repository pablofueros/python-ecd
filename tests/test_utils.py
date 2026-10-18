import os
import stat
from pathlib import Path

import pytest

from python_ecd import utils
from python_ecd.target import ChallengeTarget

EVENT_TARGET = ChallengeTarget(category="event", edition=2025, quest=1)


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


def test_find_base_recognizes_story_only_workspace(tmp_path, monkeypatch):
    nested = tmp_path / "stories/3/quest_01"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert utils.find_base() == tmp_path


def test_set_token_creates_private_global_file(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)

    result = utils.set_token("  test-token  ")

    assert result == token_path
    assert token_path.read_text() == "test-token\n"
    if os.name != "nt":
        assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700
        assert stat.S_IMODE(token_path.stat().st_mode) == 0o600


def test_has_token_prefers_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "TOKEN_PATH", tmp_path / "missing-token")
    monkeypatch.setenv("ECD_TOKEN", "environment-token")

    assert utils.has_token()


def test_has_token_reads_global_file(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("global-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.delenv("ECD_TOKEN", raising=False)

    assert utils.has_token()


def test_get_token_prefers_environment_without_modifying_file(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("stored-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.setenv("ECD_TOKEN", "environment-token")

    assert utils.get_token() == "environment-token"
    assert utils.get_token_source() == "environment"
    assert token_path.read_text() == "stored-token\n"


def test_check_token_calls_profile_endpoint_without_writing(tmp_path, monkeypatch):
    token_path = tmp_path / "missing-token"
    requests = []
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.setenv("ECD_TOKEN", "test-token")

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    def open_request(request, timeout):
        requests.append((request, timeout))
        return Response()

    monkeypatch.setattr(utils.urllib.request, "urlopen", open_request)

    utils.check_token()

    request, timeout = requests[0]
    assert request.full_url == utils.TOKEN_CHECK_URL
    assert request.get_header("Cookie") == "everybody-codes=test-token"
    assert timeout == 10
    assert not token_path.exists()


def test_remove_token_is_idempotent(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("stored-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)

    assert utils.remove_token()
    assert not utils.remove_token()


def test_execute_part_loads_solution_and_data(tmp_path):
    write_solution(tmp_path, "def part_1(data):\n    return data.upper()\n")

    assert utils.execute_part(tmp_path, EVENT_TARGET, 1) == "ABC"


def test_execute_part_rejects_missing_callable(tmp_path):
    write_solution(tmp_path, "part_1 = 'not callable'\n")

    with pytest.raises(TypeError, match="No callable 'part_1'"):
        utils.execute_part(tmp_path, EVENT_TARGET, 1)


def test_challenge_target_builds_category_paths():
    event = ChallengeTarget(category="event", edition=2025, quest=1)
    story = ChallengeTarget(category="story", edition=3, quest=2)

    assert event.relative_dir == Path("events/2025/quest_01")
    assert event.label == "Event 2025 Quest 1"
    assert story.relative_dir == Path("stories/3/quest_02")
    assert story.label == "Story 3 Quest 2"


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
