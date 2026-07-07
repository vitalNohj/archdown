import json

from archdown.state import (
    add_managed_packages,
    default_state_path,
    load_managed_package_versions,
    load_managed_packages,
    remove_managed_packages,
    update_managed_package_versions,
)


def test_managed_package_state_adds_and_removes_names(tmp_path):
    path = tmp_path / "managed.json"
    add_managed_packages(["ripgrep", "fd", "ripgrep"], path=path)
    assert load_managed_packages(path=path) == {"fd", "ripgrep"}

    remove_managed_packages(["fd"], path=path)
    assert load_managed_packages(path=path) == {"ripgrep"}


def test_managed_package_state_migrates_old_name_only_json_and_persists_versions(tmp_path):
    path = tmp_path / "managed.json"
    path.write_text(json.dumps({"packages": ["ripgrep", "fd"]}))

    changes = update_managed_package_versions({"ripgrep": "14.1.1-1", "fd": "10.3.0-1"}, {"ripgrep", "fd"}, path=path)

    assert changes == {}
    assert load_managed_packages(path=path) == {"ripgrep", "fd"}
    assert load_managed_package_versions(path=path) == {"fd": "10.3.0-1", "ripgrep": "14.1.1-1"}


def test_update_managed_package_versions_reports_only_existing_version_changes(tmp_path):
    path = tmp_path / "managed.json"
    update_managed_package_versions({"ripgrep": "14.1.1-1", "fd": "10.3.0-1"}, {"ripgrep", "fd"}, path=path)

    changes = update_managed_package_versions({"ripgrep": "14.2.0-1", "fd": "10.3.0-1", "firefox": "152.0.4-1"}, {"ripgrep", "fd"}, path=path)

    assert changes == {"ripgrep": ("14.1.1-1", "14.2.0-1")}
    assert load_managed_package_versions(path=path) == {"fd": "10.3.0-1", "ripgrep": "14.2.0-1"}


def test_default_state_path_uses_xdg_state_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert default_state_path() == tmp_path / "archdown" / "managed-packages.json"
