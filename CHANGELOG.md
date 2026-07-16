# Changelog

All notable changes to archdown are documented here.

## [0.2.0] - 2026-07-16

### Added

- Homebrew-style, read-only **update** reporting with **upgrade** as the only full-system upgrade verb.
- Structured **outdated**, **cleanup**, **which**, and **uses** commands.
- Managed-package adoption, grouping, and recently-updated markers.
- Friendly success, empty, and missing-result messages.
- The **ad** command as a short alias for **archdown**.
- **archdown --version** and automated GitHub releases with source and wheel artifacts.

### Fixed

- Detection of yay/paru's **(Installed)** search marker.
- Failure handling for update checks and empty structured output.

## [0.1.0] - 2026-07-08

### Added

- Initial Arch package-management wrapper with install, uninstall, search, info, list, refresh, upgrade, doctor, and dry-run support.

[0.2.0]: https://github.com/vitalNohj/archdown/releases/tag/v0.2.0
[0.1.0]: https://github.com/vitalNohj/archdown/commit/f5c1002
