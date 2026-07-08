import json
import subprocess

import pytest

from archdown.cli import build_parser, make_backend, print_doctor, resolve_outdated_command, run_list, run_outdated, select_backend


def test_make_backend_yay_mapping():
    backend = make_backend("yay")
    assert backend.install == ["yay", "-S"]
    assert backend.uninstall == ["yay", "-Rns"]
    assert backend.search == ["yay", "-Ss"]
    assert backend.list_installed == ["yay", "-Qe"]
    assert backend.refresh == ["yay", "-Sy"]
    assert backend.upgrade == ["yay", "-Syu"]
    assert backend.info == ["yay", "-Si"]
    assert backend.outdated == ["yay", "-Qu"]


def test_make_backend_pacman_mapping():
    backend = make_backend("pacman")
    assert backend.install == ["sudo", "pacman", "-S"]
    assert backend.uninstall == ["sudo", "pacman", "-Rns"]
    assert backend.search == ["pacman", "-Ss"]
    assert backend.list_installed == ["pacman", "-Qe"]
    assert backend.refresh == ["sudo", "pacman", "-Sy"]
    assert backend.upgrade == ["sudo", "pacman", "-Syu"]
    assert backend.info == ["pacman", "-Si"]
    assert backend.outdated == ["pacman", "-Qu"]


def test_select_backend_auto_prefers_paru(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "paru" else None)
    backend = select_backend("auto")
    assert backend.name == "paru"


def test_select_backend_auto_falls_back_to_yay(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "yay" else None)
    backend = select_backend("auto")
    assert backend.name == "yay"


def test_select_backend_auto_falls_back_to_pacman(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "pacman" else None)
    backend = select_backend("auto")
    assert backend.name == "pacman"


def test_select_backend_errors_when_requested_backend_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(SystemExit, match="Requested backend 'yay' is not installed"):
        select_backend("yay")


def test_select_backend_errors_when_no_backend_exists(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(SystemExit, match="archdown could not find paru, yay, or pacman in PATH"):
        select_backend("auto")


def test_parser_accepts_info_doctor_and_search_options():
    parser = build_parser()
    parsed = parser.parse_args(["info", "ripgrep", "--raw", "--no-color"])
    assert parsed.command == "info"
    assert parsed.package == "ripgrep"
    assert parsed.raw is True
    assert parsed.no_color is True

    parsed = parser.parse_args(["doctor"])
    assert parsed.command == "doctor"

    parsed = parser.parse_args(["search", "claude", "--raw", "--no-color"])
    assert parsed.command == "search"
    assert parsed.query == ["claude"]
    assert parsed.raw is True
    assert parsed.no_color is True

    parsed = parser.parse_args(["list", "--raw", "--no-color", "--sort", "managed", "--group", "managed", "--columns", "4"])
    assert parsed.command == "list"
    assert parsed.raw is True
    assert parsed.no_color is True
    assert parsed.sort == "managed"
    assert parsed.group == "managed"
    assert parsed.columns == 4

    parsed = parser.parse_args(["adopt", "ripgrep", "fd", "--dry-run"])
    assert parsed.command == "adopt"
    assert parsed.packages == ["ripgrep", "fd"]
    assert parsed.dry_run is True

    parsed = parser.parse_args(["adopt", "--from-current"])
    assert parsed.command == "adopt"
    assert parsed.from_current is True

    parsed = parser.parse_args(["outdated"])
    assert parsed.command == "outdated"


def test_outdated_subparser_rejects_flags_and_positionals():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["outdated", "ripgrep"])
    with pytest.raises(SystemExit):
        parser.parse_args(["outdated", "--raw"])


def test_resolve_outdated_command_prefers_checkupdates_only_for_pacman(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "checkupdates" else None)
    assert resolve_outdated_command(make_backend("pacman")) == ["checkupdates"]
    assert resolve_outdated_command(make_backend("yay")) == ["yay", "-Qu"]

    monkeypatch.setattr("shutil.which", lambda name: None)
    assert resolve_outdated_command(make_backend("pacman")) == ["pacman", "-Qu"]


def test_run_outdated_renders_transitions(monkeypatch, capsys):
    output = "ripgrep 14.1.1-1 -> 14.2.0-1\nfd 10.2.0-1 -> 10.3.0-1\n"
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, output, ""))

    assert run_outdated(["pacman", "-Qu"], dry_run=False) == 0
    out = capsys.readouterr().out
    assert "Outdated packages" in out
    assert "ripgrep" in out
    assert "14.1.1-1 -> 14.2.0-1" in out


def test_run_outdated_reports_up_to_date_on_empty_output(monkeypatch, capsys):
    # pacman -Qu / checkupdates exit non-zero with no stdout when nothing is outdated.
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", ""))

    assert run_outdated(["pacman", "-Qu"], dry_run=False) == 0
    assert capsys.readouterr().out.strip() == "Everything is up to date."


def test_run_outdated_dry_run_prints_command_without_executing(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr(subprocess, "run", fail)
    assert run_outdated(["pacman", "-Qu"], dry_run=True) == 0
    assert capsys.readouterr().out.strip() == "backend command: pacman -Qu"


def test_doctor_prints_selected_backend_and_mappings(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name in {"yay", "pacman"} else None)
    backend = make_backend("yay")
    print_doctor(backend)
    out = capsys.readouterr().out
    assert "selected backend: yay" in out
    assert "- paru: missing" in out
    assert "- yay: found" in out
    assert "- pacman: found" in out
    assert "- info: yay -Si <pkg>" in out


def test_run_list_tracks_managed_version_changes_and_leaves_raw_mode_unchanged(monkeypatch, tmp_path, capsys):
    state_path = tmp_path / "archdown" / "managed-packages.json"
    state_path.parent.mkdir()
    state_path.write_text(json.dumps({"packages": ["ripgrep"], "versions": {"ripgrep": "14.1.1-1"}}))
    backend_output = "ripgrep 14.2.0-1\nfd 10.3.0-1\n"

    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, backend_output, ""))

    assert run_list(["pacman", "-Qe"], dry_run=False, raw=False, color=False, sort="name", group="type", columns=3) == 0

    out = capsys.readouterr().out
    assert "ripgrep (Recently Updated 14.1.1-1 -> 14.2.0-1)" in out
    assert json.loads(state_path.read_text())["versions"] == {"ripgrep": "14.2.0-1"}

    assert run_list(["pacman", "-Qe"], dry_run=False, raw=True, color=False, sort="name", group="type", columns=3) == 0
    assert capsys.readouterr().out == backend_output
