from importlib.metadata import version

import pytest
from typer.testing import CliRunner

from python_ecd import utils
from python_ecd.cli import app

runner = CliRunner()


def invoke_in_workspace(tmp_path, monkeypatch, arguments):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "events").mkdir()
    return runner.invoke(app, arguments)


def test_help_and_version():
    assert runner.invoke(app, ["--help"]).exit_code == 0
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"python-ecd {version('python-ecd')}"


def test_init_creates_workspace_from_packaged_templates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "create_git", lambda path: None)

    result = runner.invoke(app, ["init", "workspace"], input="\n")

    assert result.exit_code == 0, result.output
    workspace = tmp_path / "workspace"
    assert (workspace / "events").is_dir()
    assert ".env" in (workspace / ".gitignore").read_text()
    assert "Everybody Codes Solutions" in (workspace / "README.md").read_text()
    assert not (workspace / ".env").exists()


def test_init_force_overwrites_templates(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".gitignore").write_text("old")
    (workspace / "README.md").write_text("old")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "create_git", lambda path: None)

    result = runner.invoke(app, ["init", "workspace", "--force"], input="\n")

    assert result.exit_code == 0, result.output
    assert (workspace / ".gitignore").read_text() != "old"
    assert (workspace / "README.md").read_text() != "old"


def test_set_token_does_not_print_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "events").mkdir()
    secret = "secret-value-that-must-not-leak"

    result = runner.invoke(app, ["set-token", secret])

    assert result.exit_code == 0
    assert secret not in result.output
    assert secret in (tmp_path / ".env").read_text()


def test_pull_without_token_never_calls_network(tmp_path, monkeypatch):
    monkeypatch.delenv("ECD_TOKEN", raising=False)
    monkeypatch.setattr(utils, "get_token", lambda base_dir: None)
    monkeypatch.setattr(
        utils,
        "download_input",
        lambda *args: pytest.fail("network adapter must not be called"),
    )

    result = invoke_in_workspace(tmp_path, monkeypatch, ["pull", "1"])

    assert result.exit_code == 1
    assert "Session token not found" in result.output


def test_pull_uses_adapter_double_and_creates_quest(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "get_token", lambda base_dir: "test-token")
    monkeypatch.setattr(utils, "download_input", lambda year, quest: {"1": "example"})

    result = invoke_in_workspace(tmp_path, monkeypatch, ["pull", "1", "--year", "2025"])

    assert result.exit_code == 0, result.output
    quest = tmp_path / "events/2025/quest_01"
    assert (quest / "input/input_p1.txt").read_text() == "example"
    assert (quest / "test/test_p1.txt").is_file()
    assert "def part_1" in (quest / "solution.py").read_text()


def test_pull_reports_adapter_error_without_traceback(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "get_token", lambda base_dir: "test-token")

    def fail_download(year, quest):
        raise RuntimeError("service unavailable")

    monkeypatch.setattr(utils, "download_input", fail_download)
    result = invoke_in_workspace(tmp_path, monkeypatch, ["pull", "1"])

    assert result.exit_code == 1
    assert "Failed to fetch input: service unavailable" in result.output


def test_push_reports_incorrect_answer(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "get_token", lambda base_dir: "test-token")
    monkeypatch.setattr(utils, "push_solution", lambda *args: {"correct": False})

    result = invoke_in_workspace(tmp_path, monkeypatch, ["push", "1", "--year", "2025"])

    assert result.exit_code == 0, result.output
    assert "Incorrect answer" in result.stdout


def test_push_correct_answer_downloads_next_part(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "get_token", lambda base_dir: "test-token")
    monkeypatch.setattr(
        utils,
        "push_solution",
        lambda *args: {
            "correct": True,
            "globalPlace": 1,
            "globalScore": 100,
            "globalTime": 1000,
            "localTime": 2000,
        },
    )
    monkeypatch.setattr(utils, "download_input", lambda year, quest: {"2": "next-part"})

    result = invoke_in_workspace(
        tmp_path,
        monkeypatch,
        ["push", "1", "--year", "2025", "--part", "1"],
    )

    assert result.exit_code == 0, result.output
    quest = tmp_path / "events/2025/quest_01"
    assert (quest / "input/input_p2.txt").read_text() == "next-part"
    assert (quest / "test/test_p2.txt").is_file()
