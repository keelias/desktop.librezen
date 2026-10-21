# Branding, paths, packaging, and installation

_Last reviewed: 2026-10-20._

## Current identity contract

| Surface | LibreZen identity | Notes |
| --- | --- | --- |
| Product name | LibreZen / LibreZen Browser | Use LibreZen for the application name, and LibreZen Browser in descriptive UI. |
| Source repository | keelias/desktop.librezen | Upstream Zen and Mozilla references remain where they describe inherited code or attribution. |
| Project umbrella / vendor | Volcan | LibreZen is the product; Volcan is the umbrella behind it. |
| Surfer application ID / distribution ID | systems.volcan.librezen | Reverse-domain identity derived from Penny's volcan.systems domain; it does not replace Mozilla's Firefox engine ID. |
| User command | librezen | Intended for the future Linux archive installer. |
| Internal engine binary | zen | Deliberately retained in this first branding pass because inherited AppDir/build workflows still expect that filename. Do not rename by blanket replacement. |
| Archive layout | zen/ at the archive root | Confirmed by the lower-level Mozilla mach package output. |
| XDG app directory component | librezen | The tracked nsXREDirProvider.cpp patch lowercases the configured app name before constructing the app-specific directory. This expected path behavior must be verified after rebuilding. |

The build configuration uses LibreZen as the product name, Volcan as the vendor/umbrella, systems.volcan.librezen as the Surfer application ID and distribution ID, and this repository as MOZ_SOURCE_REPO. The browser/moz.configure patch sets Firefox's implied MOZ_APP_VENDOR to Volcan (it cannot be directly exported from mozconfig on this Firefox source revision). The profile and user-appdir defaults are both explicitly set to librezen in the tracked toolkit patch so a future import preserves profile isolation. On 2026-10-21, `npm run import` completed successfully with all 268 git patches applied; after building and packaging, both `engine/obj-x86_64-pc-linux-gnu/dist/bin/application.ini` and `engine/obj-x86_64-pc-linux-gnu/dist/zen/application.ini` reported `Vendor=Volcan`, `Name=LibreZen`, `Version=1.0.0`, and `Profile=librezen`. The packaged browser was then launched with a temporary HOME and XDG directories; `about:support` reported `Name=LibreZen` and a profile under `/tmp/librezen-smoke.*/.config/librezen/`, confirming runtime profile isolation during the smoke test. The `Distribution ID` display on `about:support` was blank in this manual source-build test; this is separate from the verified `Vendor=Volcan` application metadata. Desktop-launcher and installer behavior still require testing.

The lowercase XDG paths to verify in a fresh test profile are:

- $XDG_CONFIG_HOME/librezen (normally ~/.config/librezen)
- $XDG_CACHE_HOME/librezen (normally ~/.cache/librezen)
- $XDG_DATA_HOME/librezen (normally ~/.local/share/librezen)
- $XDG_STATE_HOME/librezen (normally ~/.local/state/librezen)

These are expectations based on the tracked path patch, not a guarantee that every Firefox/Zen profile component uses all four paths. Verify them with a newly rebuilt browser and about:support / a temporary XDG environment before treating them as final. Do not move, delete, or reuse any existing Zen Browser or LibreWolf profile.

## Linux archive and install locations

The lower-level command that was tested was Mozilla's packaging target, not an Arch package builder:

    cd engine
    python3 ./mach package

It produced an archive of the form engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz. The tested archive was 103,852,308 bytes and launched after being extracted to a temporary directory with an isolated HOME/profile. It is a browser bundle, **not** a .pkg.tar.zst, AppImage, Flatpak, or ready-to-publish release.

The archive path is being validated before an installer is added. The intended manual archive layout is:

| Scope | Browser files | Launcher | Desktop entry |
| --- | --- | --- | --- |
| User-wide | ~/.local/opt/librezen/ | ~/.local/bin/librezen | $XDG_DATA_HOME/applications/librezen.desktop (defaults to ~/.local/share/applications/) |
| System-wide manual install | /opt/librezen/ | /usr/local/bin/librezen | /usr/local/share/applications/librezen.desktop |

The desktop-entry template lives at `packaging/linux/librezen.desktop`; it uses `Exec=librezen %U`, `Icon=librezen`, and identifies LibreZen as a Volcan project. The installer/package still needs to install the matching icon and launcher command at the appropriate user-wide or system-wide locations. The future installer must validate that the archive is a LibreZen build before installing it, keep program files separate from browser data, and remove only files it owns during uninstall. A profile/config/cache directory must never be deleted by the program uninstaller.

The inherited AppImage and Flatpak workflows are **not release-ready**. They still contain Zen-specific naming and deployment assumptions, including an upstream Zen Flatpak repository. Do not trigger the inherited release workflow to publish a LibreZen release until it has been audited and reworked.

## Build and test after the identity change

Use the repository's pinned Node, Python, and Rust versions. After pulling the identity changes:

1. Run npm run import so the tracked patches/configuration are applied to the generated engine tree.
2. Run the full build. The previous successful path used env SCCACHE_C_CUSTOM_CACHE_BUSTER=librezen-path-fix-20261016 npm run build to work around stale local build paths.
3. Run cd engine && python3 ./mach package.
4. Inspect application.ini in the archive. It should report Name=LibreZen, Vendor=LibreZen, and this project's source repository.
5. Launch only in a temporary directory with a temporary HOME/profile. Verify app identity, XDG paths, a second launch, and the WebGL permission flow.

The release-oriented npm run package command uses Surfer to create MAR/update files in addition to the browser archive. Its release channel must be explicitly configured; generating update metadata does not mean a working LibreZen update server or published GitHub release exists.

## Arch Linux direction

For Penny's CachyOS system, the most immediate install method is a validated tar archive with user-wide and system-wide destinations as above. That installer is not yet part of this identity commit. A native Arch package/PKGBUILD remains a good next step once the Linux bundle and paths have been tested; it should own only application files, the launcher, desktop entry, and icon—not browser profiles.
