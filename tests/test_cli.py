import pytest

from archdown.cli import build_parser, make_backend, print_doctor, select_backend


def test_make_backend_yay_mapping():
    backend = make_backend("yay")
    assert backend.install == ["yay", "-S"]
    assert backend.uninstall == ["yay", "-Rns"]
    assert backend.search == ["yay", "-Ss"]
    assert backend.list_installed == ["yay", "-Qe"]
    assert backend.refresh == ["yay", "-Sy"]
    assert backend.upgrade == ["yay", "-Syu"]
    assert backend.info == ["yay", "-Si"]


def test_make_backend_pacman_mapping():
    backend = make_backend("pacman")
    assert backend.install == ["sudo", "pacman", "-S"]
    assert backend.uninstall == ["sudo", "pacman", "-Rns"]
    assert backend.search == ["pacman", "-Ss"]
    assert backend.list_installed == ["pacman", "-Qe"]
    assert backend.refresh == ["sudo", "pacman", "-Sy"]
    assert backend.upgrade == ["sudo", "pacman", "-Syu"]
    assert backend.info == ["pacman", "-Si"]


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
    parsed = parser.parse_args(["info", "ripgrep"])
    assert parsed.command == "info"
    assert parsed.package == "ripgrep"

    parsed = parser.parse_args(["doctor"])
    assert parsed.command == "doctor"

    parsed = parser.parse_args(["search", "claude", "--raw", "--no-color"])
    assert parsed.command == "search"
    assert parsed.query == ["claude"]
    assert parsed.raw is True
    assert parsed.no_color is True


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
