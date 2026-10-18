from importlib.metadata import version

import pytest
from typer.testing import CliRunner

from python_ecd import utils
from python_ecd.cli import app

runner = CliRunner()


def invoke_in_workspace(tmp_path, monkeypatch, arguments):
    monkeypatch.chdir(tmp_path)
    utils.create_workspace_state(tmp_path)
    return runner.invoke(app, arguments)


def test_help_and_version():
    assert runner.invoke(app, ["--help"]).exit_code == 0
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"python-ecd {version('python-ecd')}"

    short_option = runner.invoke(app, ["-v"])
    assert short_option.exit_code == 2
    assert "No such option: -v" in short_option.output


def test_init_creates_workspace_from_packaged_templates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "create_git", lambda path: None)

    result = runner.invoke(app, ["init", "workspace"])

    assert result.exit_code == 0, result.output
    workspace = tmp_path / "workspace"
    assert not (workspace / "events").exists()
    assert not (workspace / "stories").exists()
    assert (workspace / ".ecd.toml").read_text() == "schema_version = 1\n"
    assert ".env" in (workspace / ".gitignore").read_text()
    assert "Everybody Codes Solutions" in (workspace / "README.md").read_text()
    assert not (workspace / ".env").exists()


def test_init_does_not_create_token_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "create_git", lambda path: None)
    token_path = tmp_path / "config/ecd/token"
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)

    result = runner.invoke(app, ["init", "workspace"])

    assert result.exit_code == 0, result.output
    assert not token_path.exists()
    assert not (tmp_path / ".env").exists()


def test_init_no_git_does_not_initialize_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        utils,
        "create_git",
        lambda path: pytest.fail("--no-git must not initialize Git"),
    )

    result = runner.invoke(app, ["init", "workspace", "--no-git"])

    assert result.exit_code == 0, result.output
    workspace = tmp_path / "workspace"
    assert (workspace / ".ecd.toml").is_file()
    assert not (workspace / ".git").exists()


def test_init_preserves_existing_files_without_force(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".gitignore").write_text("old-ignore")
    (workspace / "README.md").write_text("old-readme")
    (workspace / ".env").write_text("ECD_TOKEN=old-token\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "create_git", lambda path: None)

    result = runner.invoke(app, ["init", "workspace"])

    assert result.exit_code == 0, result.output
    assert (workspace / ".gitignore").read_text() == "old-ignore"
    assert (workspace / "README.md").read_text() == "old-readme"
    assert (workspace / ".env").read_text() == "ECD_TOKEN=old-token\n"
    assert "Legacy .env detected" in result.output
    assert "old-token" not in result.output


def test_init_migrates_legacy_workspace_without_changing_other_files(
    tmp_path, monkeypatch
):
    workspace = tmp_path / "workspace"
    (workspace / "events/2024").mkdir(parents=True)
    (workspace / "README.md").write_text("custom-readme")
    (workspace / ".env").write_text("ECD_TOKEN=legacy-secret\n")
    monkeypatch.chdir(workspace)
    monkeypatch.setattr(
        utils,
        "create_git",
        lambda path: pytest.fail("migration must not initialize Git"),
    )

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0, result.output
    assert "🧭 .ecd.toml created" in result.output
    assert "Legacy .env detected" in result.output
    assert "ecd token set" in result.output
    assert "legacy-secret" not in result.output
    assert (workspace / ".ecd.toml").read_text() == "schema_version = 1\n"
    assert (workspace / "README.md").read_text() == "custom-readme"
    assert (workspace / ".env").read_text() == "ECD_TOKEN=legacy-secret\n"
    assert not (workspace / ".gitignore").exists()


def test_init_force_overwrites_templates(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".gitignore").write_text("old")
    (workspace / "README.md").write_text("old")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "create_git", lambda path: None)

    result = runner.invoke(app, ["init", "workspace", "--force"])

    assert result.exit_code == 0, result.output
    assert (workspace / ".gitignore").read_text() != "old"
    assert (workspace / "README.md").read_text() != "old"


def test_token_set_does_not_print_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    token_path = tmp_path / "config/ecd/token"
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.delenv("ECD_TOKEN", raising=False)
    secret = "secret-value-that-must-not-leak"

    result = runner.invoke(app, ["token", "set"], input=f"{secret}\n")

    assert result.exit_code == 0, result.output
    assert secret not in result.output
    assert token_path.read_text() == f"{secret}\n"


def test_token_set_preserves_existing_file_without_force(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("old-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)

    result = runner.invoke(app, ["token", "set"])

    assert result.exit_code == 0, result.output
    assert "already exists" in result.output
    assert token_path.read_text() == "old-token\n"


def test_token_set_force_overwrites_existing_file(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("old-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    secret = "replacement-token"

    result = runner.invoke(app, ["token", "set", "--force"], input=f"{secret}\n")

    assert result.exit_code == 0, result.output
    assert secret not in result.output
    assert token_path.read_text() == f"{secret}\n"


def test_token_status_reports_environment_without_secret(tmp_path, monkeypatch):
    secret = "environment-token-that-must-not-leak"
    monkeypatch.setenv("ECD_TOKEN", secret)
    monkeypatch.setattr(utils, "TOKEN_PATH", tmp_path / "missing-token")

    result = runner.invoke(app, ["token", "status"])

    assert result.exit_code == 0, result.output
    assert "ECD_TOKEN" in result.output
    assert secret not in result.output


def test_token_status_reports_private_file(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.delenv("ECD_TOKEN", raising=False)
    utils.set_token("stored-token")

    result = runner.invoke(app, ["token", "status"])

    assert result.exit_code == 0, result.output
    assert str(token_path) in result.output
    if utils.os.name != "nt":
        assert "private (0600)" in result.output
    assert "stored-token" not in result.output


def test_token_check_uses_adapter_without_exposing_secret(tmp_path, monkeypatch):
    secret = "valid-token-that-must-not-leak"
    calls = []
    monkeypatch.setenv("ECD_TOKEN", secret)
    monkeypatch.setattr(utils, "check_token", lambda: calls.append(True))

    result = runner.invoke(app, ["token", "check"])

    assert result.exit_code == 0, result.output
    assert calls == [True]
    assert "Token is valid" in result.output
    assert secret not in result.output


def test_token_check_reports_failure_without_traceback(monkeypatch):
    monkeypatch.setenv("ECD_TOKEN", "invalid-token")

    def fail_check():
        raise RuntimeError("Everybody Codes returned HTTP 401")

    monkeypatch.setattr(utils, "check_token", fail_check)

    result = runner.invoke(app, ["token", "check"])

    assert result.exit_code == 1
    assert "Token check failed" in result.output
    assert "401" in result.output


def test_token_check_without_token_never_calls_network(tmp_path, monkeypatch):
    monkeypatch.delenv("ECD_TOKEN", raising=False)
    monkeypatch.setattr(utils, "TOKEN_PATH", tmp_path / "missing-token")
    monkeypatch.setattr(
        utils,
        "check_token",
        lambda: pytest.fail("network adapter must not be called"),
    )

    result = runner.invoke(app, ["token", "check"])

    assert result.exit_code == 1
    assert "Session token not found" in result.output


def test_token_remove_deletes_only_stored_file(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("stored-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.setenv("ECD_TOKEN", "environment-token")

    result = runner.invoke(app, ["token", "remove", "--force"])

    assert result.exit_code == 0, result.output
    assert not token_path.exists()
    assert "ECD_TOKEN remains configured" in result.output


def test_token_remove_cancel_preserves_stored_file(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("stored-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)

    result = runner.invoke(app, ["token", "remove"], input="n\n")

    assert result.exit_code == 0, result.output
    assert "removal cancelled" in result.output
    assert token_path.read_text() == "stored-token\n"


@pytest.mark.skipif(utils.os.name == "nt", reason="POSIX permissions only")
def test_token_status_warns_about_insecure_file_permissions(tmp_path, monkeypatch):
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("stored-token\n")
    token_path.chmod(0o644)
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.delenv("ECD_TOKEN", raising=False)

    result = runner.invoke(app, ["token", "status"])

    assert result.exit_code == 0, result.output
    assert "permissions are not private" in result.output
    assert "stored-token" not in result.output


def test_pull_without_token_never_calls_network(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: False)
    monkeypatch.setattr(
        utils,
        "download_input",
        lambda *args: pytest.fail("network adapter must not be called"),
    )

    result = invoke_in_workspace(tmp_path, monkeypatch, ["pull", "1", "--year", "2025"])

    assert result.exit_code == 1
    assert "Session token not found" in result.output


@pytest.mark.parametrize(
    ("command", "selectors"),
    [
        (command, selectors)
        for command in ("pull", "run", "test", "push")
        for selectors in ([], ["--year", "2025", "--story", "3"])
    ],
)
def test_challenge_commands_require_exactly_one_target(
    tmp_path, monkeypatch, command, selectors
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, [command, "1", *selectors])

    assert result.exit_code == 2
    assert "Select exactly one target" in result.output


def test_pull_from_nested_directory_reads_global_token(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    nested = workspace / "events/2025"
    nested.mkdir(parents=True)
    utils.create_workspace_state(workspace)
    token_path = tmp_path / "config/ecd/token"
    token_path.parent.mkdir(parents=True)
    token_path.write_text("global-token\n")
    monkeypatch.setattr(utils, "TOKEN_PATH", token_path)
    monkeypatch.chdir(nested)
    monkeypatch.delenv("ECD_TOKEN", raising=False)
    monkeypatch.setattr(utils, "download_input", lambda target: {})

    result = runner.invoke(app, ["pull", "1", "--year", "2025"])

    assert result.exit_code == 0, result.output
    assert "Event 2025 Quest 1 ready" in result.output


def test_pull_uses_adapter_double_and_creates_quest(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: True)
    monkeypatch.setattr(utils, "download_input", lambda target: {"1": "example"})

    result = invoke_in_workspace(tmp_path, monkeypatch, ["pull", "1", "--year", "2025"])

    assert result.exit_code == 0, result.output
    quest = tmp_path / "events/2025/quest_01"
    assert (quest / "input/input_p1.txt").read_text() == "example"
    assert (quest / "test/test_p1.txt").is_file()
    assert "def part_1" in (quest / "solution.py").read_text()


def test_pull_preserves_existing_quest_files_without_force(tmp_path, monkeypatch):
    quest = tmp_path / "events/2025/quest_01"
    (quest / "input").mkdir(parents=True)
    (quest / "test").mkdir()
    (quest / "solution.py").write_text("existing solution")
    (quest / "input/input_p1.txt").write_text("existing input")
    (quest / "test/test_p1.txt").write_text("existing test")
    utils.create_workspace_state(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "has_token", lambda: True)
    monkeypatch.setattr(utils, "download_input", lambda target: {"1": "new input"})

    result = runner.invoke(app, ["pull", "1", "--year", "2025"])

    assert result.exit_code == 0, result.output
    assert (quest / "solution.py").read_text() == "existing solution"
    assert (quest / "input/input_p1.txt").read_text() == "existing input"
    assert (quest / "test/test_p1.txt").read_text() == "existing test"
    assert result.output.count("already exists") == 3


def test_pull_story_uses_story_directory_and_api_identifier(tmp_path, monkeypatch):
    targets = []
    monkeypatch.setattr(utils, "has_token", lambda: True)

    def download(target):
        targets.append(target)
        return {"1": "story-input"}

    monkeypatch.setattr(utils, "download_input", download)

    result = invoke_in_workspace(tmp_path, monkeypatch, ["pull", "2", "--story", "3"])

    assert result.exit_code == 0, result.output
    quest = tmp_path / "stories/3/quest_02"
    assert (quest / "input/input_p1.txt").read_text() == "story-input"
    assert targets[0].category == "story"
    assert targets[0].api_event == 3
    assert targets[0].quest == 2


@pytest.mark.parametrize(
    ("command", "mode", "expected"),
    [
        ("run", "input", "Result for Event 2025 Quest 1 Part 1:\nABC"),
        ("test", "test", "Test result for Event 2025 Quest 1 Part 1:\nABC"),
    ],
)
def test_execute_commands_use_expected_data(
    tmp_path, monkeypatch, command, mode, expected
):
    quest = tmp_path / "events/2025/quest_01"
    (quest / mode).mkdir(parents=True)
    (quest / "solution.py").write_text("def part_1(data):\n    return data.upper()\n")
    (quest / mode / f"{mode}_p1.txt").write_text("abc")
    utils.create_workspace_state(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, [command, "1", "--year", "2025"])

    assert result.exit_code == 0, result.output
    assert expected in result.output


@pytest.mark.parametrize(
    ("command", "message"), [("run", "execute"), ("test", "run test")]
)
def test_execute_commands_report_missing_files_without_traceback(
    tmp_path, monkeypatch, command, message
):
    utils.create_workspace_state(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, [command, "1", "--year", "2025"])

    assert result.exit_code == 1
    assert f"Failed to {message}" in result.output
    assert "Missing solution file" in result.output
    assert "Traceback" not in result.output


def test_pull_reports_adapter_error_without_traceback(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: True)

    def fail_download(target):
        raise RuntimeError("service unavailable")

    monkeypatch.setattr(utils, "download_input", fail_download)
    result = invoke_in_workspace(tmp_path, monkeypatch, ["pull", "1", "--year", "2025"])

    assert result.exit_code == 1
    assert "Failed to fetch input: service unavailable" in result.output


def test_push_reports_incorrect_answer(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: True)
    monkeypatch.setattr(utils, "push_solution", lambda *args: {"correct": False})

    result = invoke_in_workspace(tmp_path, monkeypatch, ["push", "1", "--year", "2025"])

    assert result.exit_code == 0, result.output
    assert "Incorrect answer" in result.stdout


def test_push_without_token_never_submits(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: False)
    monkeypatch.setattr(
        utils,
        "push_solution",
        lambda *args: pytest.fail("submission adapter must not be called"),
    )

    result = invoke_in_workspace(tmp_path, monkeypatch, ["push", "1", "--year", "2025"])

    assert result.exit_code == 1
    assert "Session token not found" in result.output


def test_push_reports_submission_error_without_traceback(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: True)

    def fail_submission(*args):
        raise RuntimeError("service unavailable")

    monkeypatch.setattr(utils, "push_solution", fail_submission)

    result = invoke_in_workspace(tmp_path, monkeypatch, ["push", "1", "--year", "2025"])

    assert result.exit_code == 1
    assert "Failed to submit solution" in result.output
    assert "service unavailable" in result.output
    assert "Traceback" not in result.output


def test_push_correct_answer_downloads_next_part(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: True)
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
    monkeypatch.setattr(utils, "download_input", lambda target: {"2": "next-part"})

    result = invoke_in_workspace(
        tmp_path,
        monkeypatch,
        ["push", "1", "--year", "2025", "--part", "1"],
    )

    assert result.exit_code == 0, result.output
    quest = tmp_path / "events/2025/quest_01"
    assert (quest / "input/input_p2.txt").read_text() == "next-part"
    assert (quest / "test/test_p2.txt").is_file()
    assert "quest_01 = [1]" in (tmp_path / ".ecd.toml").read_text()


def test_push_reports_error_downloading_next_part(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: True)
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

    def fail_download(target):
        raise RuntimeError("download unavailable")

    monkeypatch.setattr(utils, "download_input", fail_download)

    result = invoke_in_workspace(tmp_path, monkeypatch, ["push", "1", "--year", "2025"])

    assert result.exit_code == 1
    assert "Failed to fetch input: download unavailable" in result.output
    assert "Traceback" not in result.output


def test_push_part_three_does_not_download_another_part(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "has_token", lambda: True)
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
    monkeypatch.setattr(
        utils,
        "download_input",
        lambda target: pytest.fail("part 4 must not be downloaded"),
    )

    result = invoke_in_workspace(
        tmp_path,
        monkeypatch,
        ["push", "1", "--year", "2025", "--part", "3"],
    )

    assert result.exit_code == 0, result.output
    assert "Correct answer" in result.output
    assert "quest_01 = [3]" in (tmp_path / ".ecd.toml").read_text()


def test_legacy_workspace_requires_init_migration(tmp_path, monkeypatch):
    (tmp_path / "events").mkdir()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["progress"])

    assert result.exit_code == 1
    assert "Legacy workspace detected" in result.output
    assert "ecd init" in result.output


def test_progress_summarizes_events_and_stories(tmp_path, monkeypatch):
    utils.create_workspace_state(tmp_path)
    utils.record_completed_part(
        tmp_path, utils.ChallengeTarget(category="event", edition=2025, quest=1), 1
    )
    for part in (1, 2, 3):
        utils.record_completed_part(
            tmp_path,
            utils.ChallengeTarget(category="story", edition=3, quest=2),
            part,
        )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["progress"])

    assert result.exit_code == 0, result.output
    assert "2025: 0/1 quests complete, 1/3 parts complete" in result.output
    assert "3: 1/1 quests complete, 3/3 parts complete" in result.output
