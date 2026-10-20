# Branding, paths, packaging, and installation

_Last reviewed: 2026-10-20._

## Current identity contract

| Surface | LibreZen identity | Notes |
| --- | --- | --- |
| Product name | LibreZen / LibreZen Browser | Use LibreZen for the application name, and LibreZen Browser in descriptive UI. |
| Source repository | keelias/desktop.librezen | Upstream Zen and Mozilla references remain where they describe inherited code or attribution. |
| Surfer product ID | org.librezen.browser | This is packaging/distribution metadata; it does not replace Mozilla's Firefox engine ID. |
| User command | librezen | Intended for the future Linux archive installer. |
| Internal engine binary | zen | Deliberately retained in this first branding pass because inherited AppDir/build workflows still expect that filename. Do not rename by blanket replacement. |
| Archive layout | zen/ at the archive root | Confirmed by the lower-level Mozilla mach package output. |
| XDG app directory component | librezen | The tracked nsXREDirProvider.cpp patch lowercases the configured app name before constructing the app-specific directory. This expected path behavior must be verified after rebuilding. |

The build configuration requests MOZ_APP_BASENAME=LibreZen, distribution ID org.librezen.browser, and this repository as MOZ_SOURCE_REPO. The browser/moz.configure patch changes Firefox's implied MOZ_APP_VENDOR value to LibreZen (it cannot be directly exported from mozconfig on this Firefox source revision); a separate reversible patch changes the unofficial branding display name from Nightly to LibreZen. **Validation completed on 2026-10-20:** the latest rebuild succeeded, the newly packaged application's application.ini reported Name=LibreZen, Vendor=LibreZen, and SourceRepository=https://github.com/keelias/desktop.librezen, and the packaged browser launched from an isolated temporary profile. Some remaining Nightly strings may still appear in cosmetic UI surfaces.

The tracked path patch lowercases the configured application name. These are the intended lowercase XDG paths, but the actual paths created by the rebuilt browser **have not yet been verified**:

- $XDG_CONFIG_HOME/librezen (normally ~/.config/librezen)
- $XDG_CACHE_HOME/librezen (normally ~/.cache/librezen)
- $XDG_DATA_HOME/librezen (normally ~/.local/share/librezen)
- $XDG_STATE_HOME/librezen (normally ~/.local/state/librezen)

These are expectations based on the tracked path patch, not a guarantee that every Firefox/Zen profile component uses all four paths. Verify them with a newly rebuilt browser and about:support / a temporary XDG environment before treating them as final. Do not move, delete, or reuse any existing Zen Browser or LibreWolf profile.

## Linux archive and install locations

The lower-level command that was tested was Mozilla's packaging target, not an Arch package builder:

    cd engine
    python3 ./mach package

It produced an archive of the form engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz. The latest archive launched after being extracted to a temporary directory with an isolated HOME, XDG directories, and browser profile. It is a browser bundle, **not** a .pkg.tar.zst, AppImage, Flatpak, or ready-to-publish release.

The archive/install path still needs validation before an installer is added. The intended manual archive layout is:

| Scope | Browser files | Launcher | Desktop entry |
| --- | --- | --- | --- |
| User-wide | ~/.local/opt/librezen/ | ~/.local/bin/librezen | $XDG_DATA_HOME/applications/librezen.desktop (defaults to ~/.local/share/applications/) |
| System-wide manual install | /opt/librezen/ | /usr/local/bin/librezen | /usr/local/share/applications/librezen.desktop |

The future installer must validate that the archive is a LibreZen build before installing it, keep program files separate from browser data, and remove only files it owns during uninstall. A profile/config/cache directory must never be deleted by the program uninstaller.

The inherited AppImage and Flatpak workflows are **not release-ready**. They still contain Zen-specific naming and deployment assumptions, including an upstream Zen Flatpak repository. Do not trigger the inherited release workflow to publish a LibreZen release until it has been audited and reworked.

## Current validation status and next checks

Already completed on 2026-10-20: `npm run import` succeeded and applied the tracked patch set; the full `npm run build` succeeded; `cd engine && python3 ./mach package` produced a Linux archive; its `application.ini` reported `Name=LibreZen`, `Vendor=LibreZen`, and this project's source repository; and the browser launched from an isolated temporary HOME/profile. The WebGL permission flow was also tested and confirmed working. Do not repeat the full build unless source changes require it.

The remaining user-assisted runtime check is filesystem isolation. Extract the latest archive to a temporary directory and run it with a fresh temporary HOME plus distinct XDG config/cache/data/state directories. Then check `about:support` for the Profile Directory and inspect which of those temporary directories actually gained LibreZen files. Record paths separately for profile data, XDG config, cache, persistent data, and state; do not infer all five from `MOZ_APP_BASENAME` alone. Relaunch with the same temporary profile to ensure startup still works. Do not move, delete, or reuse any normal Zen Browser or LibreWolf profile.

The release-oriented npm run package command uses Surfer to create MAR/update files in addition to the browser archive. Its release channel must be explicitly configured; generating update metadata does not mean a working LibreZen update server or published GitHub release exists.

## Arch Linux direction

For Penny's CachyOS system, the most immediate install method is a validated tar archive with user-wide and system-wide destinations as above. That installer is not yet part of this identity commit. A native Arch package/PKGBUILD remains a good next step once the Linux bundle and paths have been tested; it should own only application files, the launcher, desktop entry, and icon—not browser profiles.
