# LibreZen branding and installation plan

## Current status

LibreZen is an experimental browser fork built from the Zen Browser codebase and Firefox. The project now includes a tested port of LibreWolf's WebGL permission prompt. It is still a source-build project: a reliable, versioned end-user installer and upgrade/uninstall flow have not yet been verified.

This document records the branding audit and proposed conventions. It deliberately does not change profile directories, application IDs, or binary names by itself; those values are consumed by browser profile discovery, desktop integration, Flatpak/AppImage packaging, updates, and other components, so they must be migrated together and tested.

## Product identity

- **Product name:** LibreZen
- **Short name:** LibreZen
- **Description:** A Zen-based browser with LibreWolf-inspired privacy and security hardening.
- **Project source:** https://github.com/keelias/desktop.librezen
- **Upstream projects:** Zen Browser and Firefox; selected security patches are ported from LibreWolf.
- **Release status:** Experimental / not yet a supported end-user release.

Do not describe LibreZen as an official Zen Browser or LibreWolf release. Keep upstream attribution and each upstream project's license notices.

## Audit findings

The current source tree still contains inherited Zen identity in several user-visible or packaging-critical places:

- README.md is still the upstream Zen Browser README.
- surfer.json uses Zen's product name, vendor, zen app/binary names, Zen release repository, and Zen update hostname.
- configs/common/mozconfig sets the application basename to Zen, distribution ID to app.zen-browser, and source repository to Zen's upstream URL.
- build/AppDir/zen.desktop identifies the app as Zen Browser and launches zen.
- build/AppDir/AppRun launches the zen binary.
- The Flatpak template uses app.zen_browser.zen, .zen persistence, Zen-specific D-Bus names, and /etc/zen configuration.
- Branding artwork and some other assets are still Zen/Firefox upstream assets.

These are audit findings, not a claim that every occurrence should simply be renamed. Some upstream assets, Firefox compatibility names, and license headers should remain where technically or legally appropriate.

## Proposed Linux identity and paths

Use one canonical application identity for new LibreZen-specific integrations, while preserving the existing Zen and LibreWolf profiles:

| Purpose | Proposed convention | Status |
|---|---|---|
| Display name | LibreZen | Target |
| Executable / command | librezen | Target; requires packaging and launch-script changes |
| Desktop entry | librezen.desktop | Target |
| Icon name | librezen | Target |
| Per-user configuration | $XDG_CONFIG_HOME/LibreZen (normally ~/.config/LibreZen) | Target; not yet wired through the browser |
| Per-user data and browser profiles | $XDG_DATA_HOME/LibreZen (normally ~/.local/share/LibreZen) | Target; profile-service behavior must be verified |
| Per-user cache | $XDG_CACHE_HOME/LibreZen (normally ~/.cache/LibreZen) | Target; cache behavior must be verified |
| System-wide application files | /opt/librezen/ | Target for a future system install |
| System-wide desktop entry | /usr/local/share/applications/librezen.desktop or package-managed /usr/share/applications/librezen.desktop | Choose according to installation method |
| System-wide icons | /usr/local/share/icons/ or package-managed /usr/share/icons/ | Choose according to installation method |
| Flatpak app ID | A new LibreZen-specific reverse-DNS ID | Not selected; choose before publishing |
| Distribution ID / D-Bus names | LibreZen-specific values | Not selected; audit all consumers first |

XDG_CONFIG_HOME, XDG_DATA_HOME, and XDG_CACHE_HOME may be customized by the user; implementations must honor them instead of assuming the defaults. Browser profiles contain important personal data, so moving or renaming their directory must be treated as a migration, not a casual branding change.

## Installation models

### User-wide install (preferred for the first manual install)

A future portable archive can be installed under ~/.local/opt/librezen/, with a launcher and desktop entry under ~/.local/bin/ and ~/.local/share/applications/. This requires no root access and affects only that account. Exact commands should be published only after the output of npm run package has been inspected and tested.

### System-wide install

A future package-manager package should own the files under /opt/librezen/ or another package-defined application directory and install the desktop entry/icons in standard system locations. Use a native Arch package (for example, a reviewed PKGBUILD/AUR package) for Arch-based systems. Do not recommend manually copying files into /usr without package ownership.

### Portable/AppImage and Flatpak

The repository has AppDir and Flatpak-related build templates, but they still contain Zen-specific identifiers and paths. They must not be presented as LibreZen installers until their names, profile isolation, launchers, metadata, permissions, updates, and uninstall behavior have been reviewed and tested.

## Work plan

1. Keep this branding audit separate from the successful WebGL security feature port.
2. Replace the inherited README with accurate LibreZen project documentation and clearly label the build/install status.
3. Inventory identity-bearing values in surfer.json, mozconfig files, application constants, launchers, desktop files, AppImage metadata, Flatpak metadata, update configuration, and any D-Bus/native-messaging identifiers.
4. Select canonical IDs and profile-location behavior before changing them.
5. Implement the identity migration as a focused patch set; test fresh profiles, existing LibreZen profiles, and coexistence with Zen and LibreWolf.
6. Build and validate a user-local install, then a package-managed system install. Document upgrade, uninstall, and profile backup/migration.
7. Only then publish end-user installation commands or a package.

## Safety rules for the migration

- Never reuse or overwrite Zen Browser or LibreWolf profile directories.
- Never move an existing profile automatically without a backup and an explicit migration plan.
- Keep generated engine/ files out of source edits; make persistent changes through the repository's source patches/configuration.
- Keep official upstream attribution, notices, and licensing intact.
- Do not claim a release artifact is installable until a clean install, launch, upgrade, and uninstall have been tested.
