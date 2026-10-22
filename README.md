<!--
   - This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at http://mozilla.org/MPL/2.0/.
-->

# LibreZen Browser

LibreZen is an experimental, independent community browser project under the Volcan umbrella. It combines the workspace- and sidebar-oriented interface of [Zen Browser](https://zen-browser.app/) with the [Mozilla Firefox](https://www.mozilla.org/firefox/) engine and selected [LibreWolf](https://librewolf.net/) privacy and security changes. Volcan is the project umbrella; LibreZen remains the product name.

LibreZen is **not** an official release of, or affiliated with, Mozilla, Zen Browser, or LibreWolf. The project is early-stage: a successful source build and package smoke test do not yet mean every privacy feature, updater, or release installer is ready for general use.

**Project links:** [Source and issues](https://github.com/keelias/desktop.librezen) · [Security policy](SECURITY.md) · [Branding and installation status](docs/branding-and-installation.md) · [Privacy and upstream services](docs/privacy-and-upstream-services.md)

## Project status

- The Firefox source revision is pinned in surfer.json; changes to upstream dependencies are imported through Surfer.
- A Linux x86-64 archive was rebuilt and packaged on 2026-10-21. Both packaged manifests report `Vendor=Volcan`, `Name=LibreZen`, `Version=1.0.0`, and `Profile=librezen`; an `about:support` smoke test confirmed runtime profile isolation under a temporary HOME/XDG config directory.
- The built-in Gecko updater is disabled by default. Update-host metadata now points away from Zen, and the intended GitHub Releases manifest URL is reserved, but no LibreZen release or signed MAR/XML update feed has been published; updates remain manual until the release pipeline is implemented and tested.
- The inherited AppImage/Flatpak release automation still contains Zen-specific deployment assumptions and must not be used to publish LibreZen releases.

## Build from source

Use the versions pinned in .nvmrc, .python-version, and .rust-toolchain. Install the repository's Node dependencies, import the tracked patch set, then build:

    npm ci
    npm run import
    env SCCACHE_C_CUSTOM_CACHE_BUSTER=librezen-path-fix-20261016 npm run build

The cache-buster shown above was needed for a previous local checkout after the source directory had been renamed; it may not be needed for every build. See the build and installation notes before creating or installing a package.

To create the lower-level Linux browser archive after a successful build:

    cd engine
    python3 ./mach package

The archive is written below `engine/obj-*/dist/`. It is a compressed application bundle, not a native Arch package. A manual archive installer is available at `scripts/install_linux.py`; run its safety/profile-preservation tests and use the local, freshly built archive for the first install.

## Install a locally built Linux archive

From the repository root, after running `npm run build` and `cd engine && python3 ./mach package`, run the installer tests:

    python3 -m unittest scripts.test_install_linux -v

Then install user-wide (no `sudo`):

    python3 scripts/install_linux.py --user engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz

The installer validates the archive, then installs browser files to `~/.local/opt/librezen/`, a launcher to `~/.local/bin/librezen`, and a desktop entry and icon under `$XDG_DATA_HOME` (normally `~/.local/share/`). The desktop entry uses the name `LibreZen`, the comment `Browse the World Wide Web with tranquility!`, and actions for opening a private window, a new window, and the Profile Manager. The launcher is available as `~/.local/bin/librezen` even when that directory is not on the shell's `PATH`. On 2026-10-21, actual-archive user-wide and system-wide install/launch/uninstall tests passed on CachyOS, and profile preservation was verified. The desktop-action additions still need to be pulled locally, tested, and checked from KDE's menu before their behavior is considered verified.

For system-wide installation, after the user install and launch have been verified:

    sudo python3 scripts/install_linux.py --system engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz

To remove an installer-managed user installation without touching browser profiles:

    python3 scripts/install_linux.py --user --uninstall

This is a manual archive install, not an Arch package, AppImage, Flatpak, signed release, or configured updater. The inherited AppImage/Flatpak release workflows are not release-ready.

## Development principles

- Persistent engine changes belong in tracked source patches/configuration, not generated files under engine/.
- Keep LibreZen browser data separate from Zen Browser and LibreWolf profiles. Never migrate or delete profile data automatically.
- Retain upstream copyright headers, license notices, and source attribution.
- Treat privacy and security work as unverified until tested in a rebuilt packaged application; inherited browser behavior can still apply.

## Upstream projects and licensing

LibreZen builds on work from [Zen Browser](https://github.com/zen-browser/desktop), [Mozilla Firefox](https://www.mozilla.org/firefox/), and [LibreWolf](https://codeberg.org/librewolf). Their names and links identify upstream projects and attribution; they do not imply endorsement. Keep the relevant license files and source notices with redistributed builds. This repository is licensed under the terms in LICENSE, and individual imported files may carry additional notices.

## Contributing

Please use the [LibreZen issue tracker](https://github.com/keelias/desktop.librezen/issues) for project-specific bugs and feature requests. For security-sensitive issues, follow SECURITY.md instead of filing a public issue.
