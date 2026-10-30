import pytest

import bump as action


@pytest.mark.parametrize(
    "current,part,expected",
    [
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "major", "2.0.0"),
        ("v0.9.9", "patch", "0.9.10"),
    ],
)
def test_bump(current, part, expected):
    assert action.bump(current, part) == expected


@pytest.mark.parametrize("bad", ["1.2", "abc", "1.2.3-beta", ""])
def test_rejects_invalid_versions(bad):
    with pytest.raises(ValueError):
        action.bump(bad, "patch")


def test_rejects_invalid_part():
    with pytest.raises(ValueError):
        action.bump("1.0.0", "huge")


def test_main_writes_output(tmp_path, monkeypatch):
    out = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("INPUT_CURRENT", "2.3.4")
    monkeypatch.setenv("INPUT_PART", "minor")
    assert action.main() == 0
    assert out.read_text() == "new-version=2.4.0\n"


def test_main_fails_on_bad_input(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setenv("INPUT_CURRENT", "nope")
    assert action.main() == 1
    assert "::error" in capsys.readouterr().out
