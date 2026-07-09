import json
import subprocess

import pytest

from archdown.cli import (
    build_parser,
    main,
    make_backend,
    print_doctor,
    resolve_outdated_command,
    resolve_uses_command,
    run_cleanup,
    run_confirmed,
    run_info,
    run_install,
    run_list,
    run_outdated,
    run_search,
    run_uninstall,
    run_uses,
    run_which,
    select_backend,
)


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
    assert backend.orphans == ["yay", "-Qtdq"]
    assert backend.owns == ["yay", "-Qo"]
    assert backend.local_info == ["yay", "-Qi"]


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
    assert backend.orphans == ["pacman", "-Qtdq"]
    assert backend.owns == ["pacman", "-Qo"]
    assert backend.local_info == ["pacman", "-Qi"]


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

    parsed = parser.parse_args(["which", "rg", "--raw", "--no-color"])
    assert parsed.command == "which"
    assert parsed.target == "rg"
    assert parsed.raw is True
    assert parsed.no_color is True

    parsed = parser.parse_args(["uses", "openssl"])
    assert parsed.command == "uses"
    assert parsed.package == "openssl"

    parsed = parser.parse_args(["outdated"])
    assert parsed.command == "outdated"

    parsed = parser.parse_args(["cleanup"])
    assert parsed.command == "cleanup"


def test_outdated_subparser_rejects_flags_and_positionals():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["outdated", "ripgrep"])
    with pytest.raises(SystemExit):
        parser.parse_args(["outdated", "--raw"])


def test_cleanup_subparser_rejects_flags_and_positionals():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["cleanup", "ripgrep"])
    with pytest.raises(SystemExit):
        parser.parse_args(["cleanup", "--raw"])


def test_which_subparser_requires_exactly_one_positional():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["which"])
    with pytest.raises(SystemExit):
        parser.parse_args(["which", "rg", "fd"])


def test_uses_subparser_requires_exactly_one_positional_and_no_flags():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["uses"])
    with pytest.raises(SystemExit):
        parser.parse_args(["uses", "openssl", "curl"])
    with pytest.raises(SystemExit):
        parser.parse_args(["uses", "openssl", "--raw"])


def test_resolve_uses_command_prefers_pactree(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "pactree" else None)
    assert resolve_uses_command(make_backend("pacman")) == (["pactree", "-r", "-l"], "pactree")

    monkeypatch.setattr("shutil.which", lambda name: None)
    assert resolve_uses_command(make_backend("yay")) == (["yay", "-Qi"], "qi")


def test_run_uses_renders_pactree_dependents(monkeypatch, capsys):
    output = "openssl\ncurl\ngit\nwget\n"
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, output, "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_uses(["pactree", "-r", "-l"], "openssl", "pactree", dry_run=False) == 0
    out = capsys.readouterr().out
    assert "Packages that depend on openssl" in out
    assert "curl" in out and "git" in out and "wget" in out
    assert calls == [["pactree", "-r", "-l", "openssl"]]


def test_run_uses_renders_required_by_from_qi(monkeypatch, capsys):
    output = "Name            : openssl\nRequired By     : curl  git\n"
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, output, ""))

    assert run_uses(["pacman", "-Qi"], "openssl", "qi", dry_run=False) == 0
    out = capsys.readouterr().out
    assert "Packages that depend on openssl" in out
    assert "curl" in out and "git" in out


def test_run_uses_reports_nothing_depends_on_empty_result(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "leaf-pkg\n", ""))

    assert run_uses(["pactree", "-r", "-l"], "leaf-pkg", "pactree", dry_run=False) == 0
    assert capsys.readouterr().out.strip() == "Nothing depends on leaf-pkg."


def test_run_uses_surfaces_backend_failure(monkeypatch, capsys):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "error: package 'nope' not found\n"),
    )

    assert run_uses(["pactree", "-r", "-l"], "nope", "pactree", dry_run=False) == 1
    captured = capsys.readouterr()
    assert "Nothing depends on" not in captured.out
    assert "could not determine what depends on nope" in captured.err
    assert "not found" in captured.err


def test_run_uses_dry_run_prints_command_without_executing(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr(subprocess, "run", fail)
    assert run_uses(["pactree", "-r", "-l"], "openssl", "pactree", dry_run=True) == 0
    assert capsys.readouterr().out.strip() == "backend command: pactree -r -l openssl"


def test_run_which_resolves_command_and_renders_owner(monkeypatch, capsys):
    monkeypatch.setattr("os.path.exists", lambda path: False)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/rg" if name == "rg" else None)
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, "/usr/bin/rg is owned by ripgrep 15.1.0-4\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_which(["pacman", "-Qo"], "rg", dry_run=False, raw=False, color=False) == 0
    out = capsys.readouterr().out
    assert "ripgrep  15.1.0-4" in out
    assert "path: /usr/bin/rg" in out
    assert calls == [["pacman", "-Qo", "/usr/bin/rg"]]


def test_run_which_uses_existing_path_without_resolving(monkeypatch, capsys):
    monkeypatch.setattr("os.path.exists", lambda path: True)

    def fail_which(name):
        raise AssertionError("existing paths must not be resolved on PATH")

    monkeypatch.setattr("shutil.which", fail_which)
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, "/usr/bin/rg is owned by ripgrep 15.1.0-4\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_which(["pacman", "-Qo"], "/usr/bin/rg", dry_run=False, raw=False, color=False) == 0
    assert calls == [["pacman", "-Qo", "/usr/bin/rg"]]


def test_run_which_reports_not_on_path(monkeypatch, capsys):
    monkeypatch.setattr("os.path.exists", lambda path: False)
    monkeypatch.setattr("shutil.which", lambda name: None)

    def fail(*args, **kwargs):
        raise AssertionError("must not query the backend when the command is not on PATH")

    monkeypatch.setattr(subprocess, "run", fail)

    assert run_which(["pacman", "-Qo"], "rg", dry_run=False, raw=False, color=False) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "'rg' not found on PATH."


def test_run_which_reports_no_owner(monkeypatch, capsys):
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "error: No package owns /tmp/loose-file\n"),
    )

    assert run_which(["pacman", "-Qo"], "/tmp/loose-file", dry_run=False, raw=False, color=False) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "No package owns '/tmp/loose-file'."


def test_run_which_raw_passes_through_backend_output(monkeypatch, capsys):
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "/usr/bin/rg is owned by ripgrep 15.1.0-4\n", ""),
    )

    assert run_which(["pacman", "-Qo"], "/usr/bin/rg", dry_run=False, raw=True, color=False) == 0
    assert capsys.readouterr().out == "/usr/bin/rg is owned by ripgrep 15.1.0-4\n"


def test_run_which_dry_run_prints_command_without_executing(monkeypatch, capsys):
    monkeypatch.setattr("os.path.exists", lambda path: False)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/rg" if name == "rg" else None)

    def fail(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr(subprocess, "run", fail)
    assert run_which(["pacman", "-Qo"], "rg", dry_run=True, raw=False, color=False) == 0
    assert capsys.readouterr().out.strip() == "backend command: pacman -Qo /usr/bin/rg"


def test_resolve_outdated_command_prefers_checkupdates_only_for_pacman(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "checkupdates" else None)
    assert resolve_outdated_command(make_backend("pacman")) == ["checkupdates"]
    assert resolve_outdated_command(make_backend("yay")) == ["yay", "-Qu"]

    monkeypatch.setattr("shutil.which", lambda name: None)
    assert resolve_outdated_command(make_backend("pacman")) == ["pacman", "-Qu"]


def test_run_confirmed_prints_success_only_after_success(monkeypatch, capsys):
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_confirmed(["sudo", "pacman", "-Syu"], dry_run=False, success_message="System update completed.") == 0
    out = capsys.readouterr().out
    assert "backend command: sudo pacman -Syu" in out
    assert "System update completed." in out
    assert calls == [["sudo", "pacman", "-Syu"]]


def test_run_confirmed_does_not_confirm_dry_run_or_failure(monkeypatch, capsys):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    assert run_confirmed(["sudo", "pacman", "-Syu"], dry_run=True, success_message="System update completed.") == 0
    assert "System update completed." not in capsys.readouterr().out

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1))
    assert run_confirmed(["sudo", "pacman", "-Syu"], dry_run=False, success_message="System update completed.") == 1
    assert "System update completed." not in capsys.readouterr().out


def test_run_install_confirms_packages_after_success(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0))

    assert run_install(["sudo", "pacman", "-S", "ripgrep", "fd"], ["ripgrep", "fd"], dry_run=False) == 0
    out = capsys.readouterr().out
    assert "backend command: sudo pacman -S ripgrep fd" in out
    assert "Installed 2 packages: ripgrep, fd." in out


def test_run_install_does_not_confirm_dry_run_or_failure(monkeypatch, capsys):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    assert run_install(["sudo", "pacman", "-S", "ripgrep"], ["ripgrep"], dry_run=True) == 0
    assert "Installed ripgrep." not in capsys.readouterr().out

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1))
    assert run_install(["sudo", "pacman", "-S", "ripgrep"], ["ripgrep"], dry_run=False) == 1
    assert "Installed ripgrep." not in capsys.readouterr().out


def test_run_uninstall_confirms_removed_package_after_success(monkeypatch, tmp_path, capsys):
    state_path = tmp_path / "archdown" / "managed-packages.json"
    state_path.parent.mkdir()
    state_path.write_text(json.dumps({"packages": ["ripgrep"], "versions": {}}))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0))

    assert run_uninstall(["sudo", "pacman", "-Rns", "ripgrep"], ["ripgrep"], dry_run=False) == 0
    out = capsys.readouterr().out
    assert "backend command: sudo pacman -Rns ripgrep" in out
    assert "Removed ripgrep." in out
    assert json.loads(state_path.read_text())["packages"] == []


def test_main_refresh_and_update_confirm_after_success(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "pacman" else None)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0))

    assert main(["--backend", "pacman", "refresh"]) == 0
    captured = capsys.readouterr()
    assert "Package databases refreshed." in captured.out
    assert "warning: refresh only syncs databases" in captured.err

    assert main(["--backend", "pacman", "update"]) == 0
    assert "System update completed." in capsys.readouterr().out


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


def test_run_outdated_checkupdates_exit_two_is_up_to_date(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 2, "", ""))

    assert run_outdated(["checkupdates"], dry_run=False) == 0
    assert capsys.readouterr().out.strip() == "Everything is up to date."


def test_run_outdated_checkupdates_error_is_surfaced(monkeypatch, capsys):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "failed to retrieve packages\n"),
    )

    assert run_outdated(["checkupdates"], dry_run=False) == 1
    captured = capsys.readouterr()
    assert "Everything is up to date." not in captured.out
    assert "could not check for outdated packages" in captured.err
    assert "failed to retrieve packages" in captured.err


def test_run_outdated_qu_error_with_stderr_is_surfaced(monkeypatch, capsys):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "error: could not lock database\n"),
    )

    assert run_outdated(["pacman", "-Qu"], dry_run=False) == 1
    captured = capsys.readouterr()
    assert "Everything is up to date." not in captured.out
    assert "could not check for outdated packages" in captured.err
    assert "could not lock database" in captured.err


def test_run_outdated_qu_unexpected_exit_code_is_surfaced(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 127, "", ""))

    assert run_outdated(["pacman", "-Qu"], dry_run=False) == 127
    assert "Everything is up to date." not in capsys.readouterr().out


def test_run_outdated_dry_run_prints_command_without_executing(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr(subprocess, "run", fail)
    assert run_outdated(["pacman", "-Qu"], dry_run=True) == 0
    assert capsys.readouterr().out.strip() == "backend command: pacman -Qu"


def test_run_cleanup_lists_then_removes_and_updates_state(monkeypatch, tmp_path, capsys):
    state_path = tmp_path / "archdown" / "managed-packages.json"
    state_path.parent.mkdir()
    state_path.write_text(json.dumps({"packages": ["orphanlib", "ripgrep"], "versions": {}}))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))

    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        if "-Qtdq" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "orphanlib\nleftover-dep\n", "")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_cleanup(["pacman", "-Qtdq"], ["sudo", "pacman", "-Rns"], dry_run=False) == 0
    out = capsys.readouterr().out
    assert "Orphaned packages to remove:" in out
    assert "- orphanlib" in out
    assert "- leftover-dep" in out
    assert "backend command: sudo pacman -Rns orphanlib leftover-dep" in out
    assert ["sudo", "pacman", "-Rns", "orphanlib", "leftover-dep"] in calls
    # Removed orphans drop out of managed state; unrelated managed packages stay.
    assert json.loads(state_path.read_text())["packages"] == ["ripgrep"]


def test_run_cleanup_reports_nothing_when_no_orphans(monkeypatch, capsys):
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        # `pacman -Qtdq` exits non-zero with empty output when there are no orphans.
        return subprocess.CompletedProcess(cmd, 1, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_cleanup(["pacman", "-Qtdq"], ["sudo", "pacman", "-Rns"], dry_run=False) == 0
    assert capsys.readouterr().out.strip() == "Nothing to clean up."
    assert calls == [["pacman", "-Qtdq"]]


def test_run_cleanup_dry_run_shows_orphans_without_removing(monkeypatch, tmp_path, capsys):
    state_path = tmp_path / "archdown" / "managed-packages.json"
    state_path.parent.mkdir()
    state_path.write_text(json.dumps({"packages": ["orphanlib"], "versions": {}}))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))

    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        if "-Qtdq" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "orphanlib\n", "")
        raise AssertionError("cleanup must not remove packages in dry-run")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_cleanup(["pacman", "-Qtdq"], ["sudo", "pacman", "-Rns"], dry_run=True) == 0
    out = capsys.readouterr().out
    assert "- orphanlib" in out
    assert "backend command: sudo pacman -Rns orphanlib" in out
    # Only the read-only query runs; no removal and managed state is untouched.
    assert calls == [["pacman", "-Qtdq"]]
    assert json.loads(state_path.read_text())["packages"] == ["orphanlib"]


def test_run_cleanup_surfaces_query_failure(monkeypatch, capsys):
    def fake_run(cmd, *args, **kwargs):
        if "-Qtdq" in cmd:
            return subprocess.CompletedProcess(cmd, 1, "", "error: could not lock database\n")
        raise AssertionError("cleanup must not remove packages after a query failure")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_cleanup(["pacman", "-Qtdq"], ["sudo", "pacman", "-Rns"], dry_run=False) == 1
    captured = capsys.readouterr()
    assert "Nothing to clean up." not in captured.out
    assert "could not check for orphaned packages" in captured.err
    assert "could not lock database" in captured.err


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
    assert "- which: yay -Qo <path>" in out
    assert "- uses: yay -Qi <pkg>" in out
    assert "- cleanup: yay -Qtdq | yay -Rns -" in out


def test_run_search_reports_no_matches_on_empty_output(monkeypatch, capsys):
    # pacman/yay/paru exit non-zero with empty stdout when a query matches nothing.
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", ""))

    assert run_search(["pacman", "-Ss", "nope"], dry_run=False, raw=False, color=False) == 1
    assert capsys.readouterr().out.strip() == "No packages found."


def test_run_search_falls_back_to_raw_when_output_unparseable(monkeypatch, capsys):
    # Non-empty output that yields no structured results must not be swallowed.
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "something weird\n", ""),
    )

    assert run_search(["pacman", "-Ss", "weird"], dry_run=False, raw=False, color=False) == 0
    out = capsys.readouterr().out
    assert "something weird" in out
    assert "No packages found." not in out


def test_run_info_reports_missing_package_without_empty_block(monkeypatch, capsys):
    # A missing package: backend prints the error to stderr, empty stdout, non-zero exit.
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "error: package 'nope' was not found\n"),
    )

    assert run_info(["pacman", "-Si", "nope"], dry_run=False, raw=False, color=False) == 1
    captured = capsys.readouterr()
    assert captured.out.strip() == "No package found."
    assert "Package information" not in captured.out
    # The backend's own error is still surfaced on stderr.
    assert "was not found" in captured.err


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
