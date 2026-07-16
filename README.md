<p align="center">
  <img src="assets/archdown-logo.svg" alt="archdown — Arch power. Friendly words." width="680">
</p>

<p align="center">
  <a href="https://github.com/vitalNohj/archdown/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/vitalNohj/archdown/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;logo=github"></a>
  <a href="https://github.com/vitalNohj/archdown/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/vitalNohj/archdown?style=flat-square&amp;logo=github"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white">
  <img alt="Arch Linux" src="https://img.shields.io/badge/Arch_Linux-native-1793D1?style=flat-square&amp;logo=archlinux&amp;logoColor=white">
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square"></a>
  <a href="CONTRIBUTING.md"><img alt="Contributions welcome" src="https://img.shields.io/badge/contributions-welcome-F59E0B?style=flat-square"></a>
</p>

<p align="center">
  <strong>A friendly command line for everyday Arch Linux package management.</strong>
  <br>
  Familiar words in front. Real <code>paru</code>, <code>yay</code>, and <code>pacman</code> underneath.
</p>

---

## Arch without the memory test

Arch is powerful. Everyday package management should not feel like a test of
how many flags you can remember.

I built Archdown to smooth out my own Arch experience. I wanted to type what I
meant—<code>search</code>, <code>install</code>, <code>update</code>,
<code>upgrade</code>—and still keep the package ecosystem and control that made
me choose Arch in the first place.

> **The mission:** make Arch friendlier without hiding Arch, replacing its
> tools, or inventing another package ecosystem.

Archdown is a small compatibility layer for humans. It chooses an available
backend, runs the real Arch tooling, and turns common workflows into memorable
commands with clearer output and safer defaults.

## Start in 30 seconds

Archdown is not in the AUR or PyPI yet. Install the current release directly
with [uv](https://docs.astral.sh/uv/):

~~~bash
sudo pacman -S --needed uv
uv tool install "git+https://github.com/vitalNohj/archdown@v0.2.0"
archdown doctor
~~~

Then try the everyday loop:

~~~bash
archdown search terminal emulator
archdown install neovim
archdown update
archdown upgrade
~~~

Prefer something shorter? The installed <code>ad</code> command is a complete
alias:

~~~bash
ad search ripgrep
ad update
~~~

> [!IMPORTANT]
> <code>archdown update</code> is read-only. It reports available updates but
> never installs them. Only <code>archdown upgrade</code> performs the full
> system upgrade.

## What feels different

| Archdown gives you | What that means |
|---|---|
| **Intent-first commands** | Remember <code>install</code>, not a collection of flags. |
| **Arch-native behavior** | Packages still come from official repositories and the AUR. |
| **Backend awareness** | Archdown prefers <code>paru</code>, then <code>yay</code>, then <code>pacman</code>. |
| **Safer update semantics** | Checking for updates and installing them are separate, explicit actions. |
| **Human output** | Results are grouped, aligned, color-aware, and clear when nothing was found. |
| **No new daemon or database** | Archdown remains a lightweight wrapper over tools you already trust. |

## The command guide

| Command | Purpose | Package-system effect |
|---|---|---|
| <code>archdown search &lt;terms&gt;</code> | Search official repositories and the AUR | Read-only |
| <code>archdown info &lt;package&gt;</code> | Show package details | Read-only |
| <code>archdown which &lt;command-or-path&gt;</code> | Find the package that owns a command or file | Read-only |
| <code>archdown uses &lt;package&gt;</code> | Show what still depends on a package | Read-only |
| <code>archdown list</code> | Browse explicitly installed packages | Read-only packages; updates local tracking |
| <code>archdown outdated</code> | List available upgrades | Read-only |
| <code>archdown update</code> | Check and report available updates | Read-only |
| <code>archdown install &lt;package...&gt;</code> | Install packages | Changes packages |
| <code>archdown uninstall &lt;package...&gt;</code> | Remove packages and unused dependencies | Changes packages |
| <code>archdown cleanup</code> | Preview and remove orphaned dependencies | Changes packages after preview |
| <code>archdown upgrade</code> | Perform a full system upgrade | Changes packages |
| <code>archdown refresh</code> | Explicitly sync live package databases | Changes package metadata; warns first |
| <code>archdown adopt &lt;package...&gt;</code> | Add existing packages to Archdown tracking | Local bookkeeping only |
| <code>archdown doctor</code> | Explain detected tools and command mappings | Read-only |

Most package-changing commands support the global <code>--dry-run</code> flag:

~~~bash
archdown --dry-run install ripgrep
archdown --dry-run cleanup
archdown --backend pacman --dry-run upgrade
~~~

## A visible safety contract

Archdown is deliberately clear about what can change your system.

### Safe to explore

<code>search</code>, <code>info</code>, <code>which</code>,
<code>uses</code>, <code>list</code>, <code>outdated</code>,
<code>update</code>, and <code>doctor</code> never install, remove, or upgrade
packages.

### Explicitly mutating

<code>install</code>, <code>uninstall</code>, <code>cleanup</code>,
<code>refresh</code>, and <code>upgrade</code> are the commands that can change
package or live database state. They expose the backend command, honor dry-run
where applicable, and only print a success message after the backend succeeds.

This split matters on Arch: a bare live database sync can create a
partial-upgrade window. That is why <code>update</code> uses safe query paths
and <code>upgrade</code> remains the one obvious verb for a full
<code>-Syu</code>.

## Update should feel calm

~~~text
$ archdown update
Outdated packages
-----------------
firefox   152.0-1       -> 153.0-1
linux     6.18.4.arch1  -> 6.18.5.arch1
ripgrep   14.1.1-1      -> 14.2.0-1

Run archdown upgrade to upgrade them.
~~~

On a current system:

~~~text
$ archdown update
Everything is up to date.
~~~

Color follows terminal capabilities and respects <code>NO_COLOR</code>.
Use <code>archdown update --no-color</code> when plain output is preferable.

## Real Arch tools, not a replacement ecosystem

Archdown automatically selects the first backend it finds:

~~~text
paru  →  yay  →  pacman
~~~

Run <code>archdown doctor</code> at any time to see what was detected and the
exact backend commands Archdown maps to. You can also force a backend:

~~~bash
archdown --backend pacman search ripgrep
archdown --backend yay update
~~~

Archdown does not replace pacman, an AUR helper, or the Arch Wiki. It gives
their most common workflows a smaller, friendlier surface.

## Project status

The current release is
[v0.2.0](https://github.com/vitalNohj/archdown/releases/tag/v0.2.0), the first
feature-complete development release.

### Working today

- Friendly install, uninstall, search, info, update, and upgrade workflows
- Official repository and AUR-aware backend selection
- Read-only outdated, ownership, and reverse-dependency queries
- Orphan cleanup with a visible preview
- Managed-package adoption and recently-updated markers
- Friendly empty states, success confirmations, color, and dry-run support
- Tested on Python 3.10, 3.11, and 3.12

### Where the project can grow

- [ ] Publish maintained AUR and PyPI packages
- [ ] Add shell completions
- [ ] Add structured JSON output
- [ ] Guide users when a preferred backend is missing
- [ ] Enrich package information and dependency views
- [ ] Keep sanding down rough Arch workflows as real users find them

Have an idea that would make Arch feel kinder? Please
[open an issue](https://github.com/vitalNohj/archdown/issues).

## Frequently asked questions

<details>
<summary><strong>Does Archdown replace pacman, yay, or paru?</strong></summary>

No. Archdown calls the real backend tools. It is a user-experience layer, not a
new package manager or repository.

</details>

<details>
<summary><strong>Is <code>archdown update</code> safe?</strong></summary>

Yes. It is read-only and never runs an upgrade or a bare live
<code>-Sy</code>. It reports what can be upgraded and points you to the
explicit <code>archdown upgrade</code> command.

</details>

<details>
<summary><strong>Does it support the AUR?</strong></summary>

Yes. Archdown uses <code>paru</code> or <code>yay</code> when available and
falls back to <code>pacman</code> for official repositories.

</details>

<details>
<summary><strong>Why not just memorize the backend flags?</strong></summary>

You absolutely can—and Archdown will never take that option away. This project
exists for people who would rather remember their intention than the spelling
of every routine operation.

</details>

<details>
<summary><strong>Is this an official Arch Linux project?</strong></summary>

No. Archdown is an independent community project and is not affiliated with or
endorsed by Arch Linux.

</details>

## A project that welcomes people

Archdown is meant to make Arch more approachable, and the project should feel
approachable too. New contributors are welcome. You do not need to be a package
manager expert to improve an error message, document a confusing workflow,
write a test, or share the friction you hit.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for the development and release loop.
- Browse the behavior-first specs in [openspec/](openspec/).
- Report bugs and propose ideas in
  [GitHub Issues](https://github.com/vitalNohj/archdown/issues).
- Check the [changelog](CHANGELOG.md) to see how the project is evolving.

### Local development

~~~bash
git clone https://github.com/vitalNohj/archdown.git
cd archdown
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
~~~

The test suite mocks package backends; it never installs, removes, or upgrades
real packages.

## License

Archdown is available under the [MIT License](LICENSE).

<p align="center">
  <strong>Made on Arch, for people who want to enjoy Arch.</strong>
</p>
