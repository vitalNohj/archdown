from archdown.state import add_managed_packages, default_state_path, load_managed_packages, remove_managed_packages


def test_managed_package_state_adds_and_removes_names(tmp_path):
    path = tmp_path / "managed.json"
    add_managed_packages(["ripgrep", "fd", "ripgrep"], path=path)
    assert load_managed_packages(path=path) == {"fd", "ripgrep"}

    remove_managed_packages(["fd"], path=path)
    assert load_managed_packages(path=path) == {"ripgrep"}


def test_default_state_path_uses_xdg_state_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert default_state_path() == tmp_path / "archdown" / "managed-packages.json"
