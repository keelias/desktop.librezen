# Branding, paths, packaging, and installation

_Last reviewed: 2026-10-21._

## Current identity contract

| Surface | LibreZen identity | Notes |
| --- | --- | --- |
| Product name | LibreZen / LibreZen Browser | Use LibreZen for the application name, and LibreZen Browser in descriptive UI. |
| Source repository | keelias/desktop.librezen | Upstream Zen and Mozilla references remain where they describe inherited code or attribution. |
| Project umbrella / vendor | Volcan | LibreZen is the product; Volcan is the umbrella behind it. |
| Surfer application ID / distribution ID | systems.volcan.librezen | Reverse-domain identity derived from Penny's volcan.systems domain; it does not replace Mozilla's Firefox engine ID. |
| User command | `librezen` | Installed as a wrapper around the internal `zen` executable. |
| Internal engine binary | zen | Deliberately retained in this first branding pass because inherited AppDir/build workflows still expect that filename. Do not rename by blanket replacement. |
| Archive layout | zen/ at the archive root | Confirmed by the lower-level Mozilla mach package output. |
| XDG app directory component | `librezen` | Confirmed at runtime: the smoke test used `$HOME/.config/librezen/<profile>` under a temporary HOME. |

The build configuration uses LibreZen as the product name, Volcan as the vendor/umbrella, systems.volcan.librezen as the Surfer application ID and distribution ID, and this repository as MOZ_SOURCE_REPO. The browser/moz.configure patch sets Firefox's implied MOZ_APP_VENDOR to Volcan (it cannot be directly exported from mozconfig on this Firefox source revision). The profile and user-appdir defaults are both explicitly set to librezen in the tracked toolkit patch so a future import preserves profile isolation. On 2026-10-21, `npm run import` completed successfully with all 268 git patches applied; after building and packaging, both `engine/obj-x86_64-pc-linux-gnu/dist/bin/application.ini` and `engine/obj-x86_64-pc-linux-gnu/dist/zen/application.ini` reported `Vendor=Volcan`, `Name=LibreZen`, `Version=1.0.0`, and `Profile=librezen`. A source-build smoke test and an installed-launcher smoke test both reported `Name=LibreZen` and used a profile under a temporary `/tmp/librezen-*/.config/librezen/` home. The installer unit suite passed all six tests, including a synthetic install/uninstall round trip that preserved unrelated profile data. The installed `/home/penny/.local/share/applications/librezen.desktop` passed `desktop-file-validate`, and launching LibreZen from KDE's application menu succeeded. That normal menu launch reported the binary `/home/penny/.local/opt/librezen/zen` and a profile under `/home/penny/.config/librezen/`, confirming the persistent LibreZen profile location is separate from Zen Browser and LibreWolf. The `Distribution ID` display on `about:support` was blank in these manual builds; this is separate from the verified `Vendor=Volcan` application metadata. On 2026-10-21, user-wide and system-wide install/uninstall round trips were completed against the actual archive. Both uninstallers removed the four installer-managed application/integration paths while preserving `/home/penny/.config/librezen/`. The user-wide installation was restored afterward; all four expected paths were present and `desktop-file-validate` passed.

The lowercase XDG paths to verify in a fresh test profile are:

- $XDG_CONFIG_HOME/librezen (normally ~/.config/librezen)
- $XDG_CACHE_HOME/librezen (normally ~/.cache/librezen)
- $XDG_DATA_HOME/librezen (normally ~/.local/share/librezen)
- $XDG_STATE_HOME/librezen (normally ~/.local/state/librezen)

These are expectations based on the tracked path patch, not a guarantee that every Firefox/Zen profile component uses all four paths. Verify them with a newly rebuilt browser and about:support / a temporary XDG environment before treating them as final. Do not move, delete, or reuse any existing Zen Browser or LibreWolf profile.

## Linux archive and install locations

The lower-level archive is built with Mozilla's packaging target, not an Arch package builder:

    cd engine
    python3 ./mach package

It produced an archive of the form engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz. The tested archive was 103,852,308 bytes and launched after being extracted to a temporary directory with an isolated HOME/profile. It is a browser bundle, **not** a .pkg.tar.zst, AppImage, Flatpak, or ready-to-publish release.

The tracked installer at `scripts/install_linux.py` validates the archive metadata and its file paths before extracting or installing anything. The user-wide install was exercised against the actual browser archive on 2026-10-21; `about:support` reported `/home/penny/.local/opt/librezen/zen` and a temporary profile under `/tmp/librezen-installed.*/.config/librezen/`. Launching from KDE's application menu also succeeded, with the normal profile under `/home/penny/.config/librezen/`. The actual-archive user-wide uninstall removed the app, launcher, desktop entry, and icon while preserving profile data. A system-wide install of the same archive then launched `/opt/librezen/zen` with a temporary profile; its uninstall removed the app, launcher, desktop entry, and icon while preserving the real user profile. The user-wide installation was then restored and its four expected paths were verified; `desktop-file-validate` passed. The intended destinations are:

| Scope | Browser files | Launcher | Desktop entry |
| --- | --- | --- | --- |
| User-wide | ~/.local/opt/librezen/ | ~/.local/bin/librezen | $XDG_DATA_HOME/applications/librezen.desktop (defaults to ~/.local/share/applications/) |
| System-wide manual install | /opt/librezen/ | /usr/local/bin/librezen | /usr/local/share/applications/librezen.desktop |

The desktop-entry template lives at `packaging/linux/librezen.desktop`. It uses `Name=LibreZen`, the comment `Browse the World Wide Web with tranquility!`, and desktop actions for opening a private window, opening a regular window, and opening the Profile Manager. The installer rewrites the main `Exec=`/`TryExec=` and each action's `Exec=` to use the absolute launcher for the selected install scope, installs the archive's bundled PNG under the `librezen` icon name, and refreshes the desktop database when that utility is available. Unit tests cover the action commands and path rewriting; after pulling this desktop-action update, rerun the tests and validate the installed desktop entry before relying on the actions from KDE's menu. The installer checks for expected `Vendor=Volcan` and `Profile=librezen` metadata, extracts only validated paths beneath the archive's `zen/` root, refuses to overwrite existing destinations, and records a checksum manifest for files it owns. The uninstaller only removes matching owned launcher/desktop/icon files and the marked application directory. Profile/config/cache data is never removed by the program uninstaller.

Install from the repository root using the archive produced by `cd engine && python3 ./mach package` (the exact versioned filename may vary):

User-wide, no `sudo`:

```sh
python3 scripts/install_linux.py --user engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz
```

System-wide, with administrator privileges:

```sh
sudo python3 scripts/install_linux.py --system engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz
```

Before installing, run the archive-safety and profile-preservation tests from the repository root:

```sh
python3 -m unittest scripts.test_install_linux -v
```

Uninstall the matching installation:

```sh
python3 scripts/install_linux.py --user --uninstall
sudo python3 scripts/install_linux.py --system --uninstall
```

To upgrade, uninstall the matching application files and install the newer validated archive. The installer deliberately refuses to overwrite pre-existing paths. If a launcher, desktop entry, or icon has been customized, the uninstaller preserves that modified file and tells you about it. Use `--user` without `sudo`; use `sudo` only for `--system`. A user-wide command can always be invoked as `~/.local/bin/librezen` even if `~/.local/bin` is not on the current shell's `PATH`. Neither install nor uninstall changes browser profiles.

The inherited AppImage and Flatpak workflows are **not release-ready**. They still contain Zen-specific naming and deployment assumptions, including an upstream Zen Flatpak repository. Do not trigger the inherited release workflow to publish a LibreZen release until it has been audited and reworked.

## Build and test after the identity change

Use the repository's pinned Node, Python, and Rust versions. After pulling the identity changes:

1. Run npm run import so the tracked patches/configuration are applied to the generated engine tree.
2. Run the full build. The previous successful path used env SCCACHE_C_CUSTOM_CACHE_BUSTER=librezen-path-fix-20261016 npm run build to work around stale local build paths.
3. Run cd engine && python3 ./mach package.
4. Inspect `application.ini`; verified output is `Name=LibreZen`, `Vendor=Volcan`, `Version=1.0.0`, and `Profile=librezen` in both manifest copies.
5. Launch only in a temporary directory with a temporary HOME/profile. Verify app identity, XDG paths, a second launch, and the WebGL permission flow.
6. Exercise the installer on the archive and confirm launcher/menu integration plus user-wide and system-wide uninstall preservation. These checks passed on CachyOS on 2026-10-21, though a fresh launch after restoring the final user-wide installation has not yet been rechecked.

The release-oriented npm run package command uses Surfer to create MAR/update files in addition to the browser archive. Its release channel must be explicitly configured; generating update metadata does not mean a working LibreZen update server or published GitHub release exists.

## Arch Linux direction

For Penny's CachyOS system, a validated tar archive can now be installed user-wide or system-wide with `scripts/install_linux.py`. On 2026-10-21, end-to-end install/launch/uninstall checks passed for both scopes against the actual archive, and the user-wide install was restored afterward. A fresh launch after restoration has not yet been rechecked. A native Arch package/PKGBUILD remains a useful next step; it should own only application files, the launcher, desktop entry, and icon—not browser profiles.
