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
- A Linux x86-64 archive was successfully generated with Mozilla's mach package target and launched in a temporary HOME/profile on 2026-10-20. That package predates the current LibreZen identity edits, so rebuild and verify before installing it.
- There is not yet a published LibreZen release or a configured LibreZen update service.
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

The archive is written below engine/obj-*/dist/. It is a compressed application bundle, not a native Arch package. The planned install script is not yet available; use the isolated smoke-test process in the installation notes rather than launching an unverified build against an existing browser profile.

## Development principles

- Persistent engine changes belong in tracked source patches/configuration, not generated files under engine/.
- Keep LibreZen browser data separate from Zen Browser and LibreWolf profiles. Never migrate or delete profile data automatically.
- Retain upstream copyright headers, license notices, and source attribution.
- Treat privacy and security work as unverified until tested in a rebuilt packaged application; inherited browser behavior can still apply.

## Upstream projects and licensing

LibreZen builds on work from [Zen Browser](https://github.com/zen-browser/desktop), [Mozilla Firefox](https://www.mozilla.org/firefox/), and [LibreWolf](https://codeberg.org/librewolf). Their names and links identify upstream projects and attribution; they do not imply endorsement. Keep the relevant license files and source notices with redistributed builds. This repository is licensed under the terms in LICENSE, and individual imported files may carry additional notices.

## Contributing

Please use the [LibreZen issue tracker](https://github.com/keelias/desktop.librezen/issues) for project-specific bugs and feature requests. For security-sensitive issues, follow SECURITY.md instead of filing a public issue.
