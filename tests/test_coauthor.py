import importlib.util
from pathlib import Path


def load_coauthor_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "coauthor.py"
    spec = importlib.util.spec_from_file_location("coauthor", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_prints_usage_when_username_missing(capsys):
    coauthor = load_coauthor_module()

    assert coauthor.main(["coauthor.py"]) == 1

    err = capsys.readouterr().err
    assert "Usage: coauthor.py <github-username>" in err


def test_main_prints_usage_for_help_flag(capsys):
    coauthor = load_coauthor_module()

    assert coauthor.main(["coauthor.py", "--help"]) == 1

    err = capsys.readouterr().err
    assert "Usage: coauthor.py <github-username>" in err


def test_main_formats_coauthor_line_with_display_name(monkeypatch, capsys):
    coauthor = load_coauthor_module()
    monkeypatch.setattr(
        coauthor,
        "fetch_user",
        lambda username: {"login": "octocat", "id": 583231, "name": "The Octocat"},
    )

    assert coauthor.main(["coauthor.py", "octocat"]) == 0

    out = capsys.readouterr().out
    assert "Co-authored-by: The Octocat <583231+octocat@users.noreply.github.com>" in out


def test_main_uses_login_when_display_name_is_missing(monkeypatch, capsys):
    coauthor = load_coauthor_module()
    monkeypatch.setattr(
        coauthor,
        "fetch_user",
        lambda username: {"login": "hubot", "id": 42, "name": None},
    )

    assert coauthor.main(["coauthor.py", "hubot"]) == 0

    out = capsys.readouterr().out
    assert "Co-authored-by: hubot <42+hubot@users.noreply.github.com>" in out


def test_main_uses_requested_username_when_api_login_is_missing(monkeypatch, capsys):
    coauthor = load_coauthor_module()
    monkeypatch.setattr(
        coauthor,
        "fetch_user",
        lambda username: {"id": 99, "name": None},
    )

    assert coauthor.main(["coauthor.py", "fallback-user"]) == 0

    out = capsys.readouterr().out
    assert "Co-authored-by: fallback-user <99+fallback-user@users.noreply.github.com>" in out


def test_main_strips_surrounding_username_whitespace(monkeypatch):
    coauthor = load_coauthor_module()
    seen = {}

    def fake_fetch(username):
        seen["username"] = username
        return {"login": username, "id": 7, "name": None}

    monkeypatch.setattr(coauthor, "fetch_user", fake_fetch)

    assert coauthor.main(["coauthor.py", "  spaced-user  "]) == 0
    assert seen["username"] == "spaced-user"


def test_main_returns_error_when_api_response_has_no_id(monkeypatch, capsys):
    coauthor = load_coauthor_module()
    monkeypatch.setattr(
        coauthor,
        "fetch_user",
        lambda username: {"login": "missing-id", "name": "Missing ID"},
    )

    assert coauthor.main(["coauthor.py", "missing-id"]) == 2

    err = capsys.readouterr().err
    assert "error: missing 'id' in API response" in err
