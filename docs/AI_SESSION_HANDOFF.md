# LibreZen — session handoff and next steps

_Last updated: 2026-10-20_

This note is a continuity aid for the next development session. Read it first, then verify the current checkout and repository state before editing anything. It records known results and the user's next requested task; it is not a substitute for inspecting the actual source.

## Project identity and goal

- Repository: [`keelias/desktop.librezen`](https://github.com/keelias/desktop.librezen).
- Known working branch: `security/librewolf-hardening`.
- Last verified remote commit at handoff time: `61fafe9fa75ccdfcf456356fc82040debaa17e8e` — `fix(security): anchor WebGL observer entries before object close`.
- LibreZen's intended product direction is **Zen Browser's frontend/UI and Mozilla Firefox base, with LibreWolf privacy/security features and options**. This is a fork/project identity, not an official Zen Browser or LibreWolf release.
- The target test machine is Penny's Arch-family PC running CachyOS. The code should ideally be maintainable and installable on Arch Linux as well, not only runnable from the source tree.

## Latest successful work: WebGL permission prompt

The first LibreWolf WebGL-permission feature port is implemented and has passed a successful build plus initial runtime testing.

Relevant source files:
- Implementation patch: `src/librezen/webgl-permission.patch`
- Documentation: `docs/security/webgl-permission.md`

Important architecture rule: this project uses Surfer patches to populate the generated `engine/` tree. Persistent changes belong in the tracked patch/source files under `src/`; do not hand-edit generated `engine/` files as the long-term fix. Re-importing regenerates/reapplies the tracked patch set.

Implementation includes the engine-side WebGL permission gate for HTML canvas and OffscreenCanvas/worker paths, a browser-process prompt helper, per-origin allow/block decisions, a remember decision option, permission-management UI, URL-bar indicators/assets, localization, and preferences:
- `librewolf.webgl.prompt = true`
- `librewolf.webgl.prompt.hide = false`
- Existing `webgl.disabled` remains the global WebGL kill switch.

Validation reported by the user:
- `npm run import` completed successfully and applied the full patch set (264 patches).
- A full `npm run build` succeeded in about 10 minutes 49 seconds.
- The user launched the compiled browser with `npm start`, tested https://get.webgl.org/, and confirmed the prompt works.
- Both session-only and persistent permission modes were tested and reported to work.

Useful remaining tests, not prerequisites for celebrating the initial port:
1. Private-window behavior: remember checkbox should not be offered, and grants should not persist beyond the private session.
2. Remembered block, removing/revoking a permission, and retrying the same origin.
3. A second origin should receive an independent decision.
4. An OffscreenCanvas/WebGL worker test, where one is available.

**Documentation follow-up:** `docs/security/webgl-permission.md` still contains a caveat saying the built binary has not yet been runtime-tested and frames all checklist steps as expectations. That was true before the recent tests and is now stale. Update it only to match tests actually performed; mark private-window/origin/worker checks separately until verified.

## Build and environment notes

Known working local checkout path from the prior session: `~/.src/librezen.source/` (on Penny's machine; verify before assuming it is still the active checkout). The generated engine is under `engine/`, with build output in `engine/obj-x86_64-pc-linux-gnu`.

Known tool versions in the environment:
- Node.js 22.23.3
- Python 3.11.17 (managed with uv)
- Rust 1.95.0

A successful full build was run as:

```sh
env SCCACHE_C_CUSTOM_CACHE_BUSTER=librezen-path-fix-20261016 npm run build
```

The cache-buster was a local build-environment workaround for stale generated make dependency paths after the project directory was renamed. Preserve the existing object directory/cache and do not run destructive cleanup/rebuild steps unnecessarily. Do not rebuild just to reconfirm what already passed.

Useful project commands from the current `package.json`:
- `npm run import` — regenerate/import the patched engine source.
- `npm run build` — build.
- `npm start` — run the development build via `python3 ./mach run --noprofile` from `engine/`.
- `cd engine && python3 ./mach package` — ran successfully on 2026-10-20 and produced `engine/obj-x86_64-pc-linux-gnu/dist/zen-1.0.0.en-US.linux-x86_64.tar.xz` (103,852,308 bytes). The archive's extracted browser launched using a temporary HOME and profile. This was a lower-level Mozilla package, not an Arch package or a finished installer.
- The smoke-test archive reported `Name=Zen`, `Vendor=Mozilla`, and `SourceRepository=https://github.com/zen-browser/desktop`; it predates the identity settings in this commit and must not be presented as a branded LibreZen release.

CachyOS is Arch-based, so advice based on `apt`/Debian packaging is not appropriate. The project's previous generic bootstrap attempts using Debian/RPM assumptions failed; inspect available tools and Surfer packaging configuration before prescribing commands.

## Next requested task: audit LibreZen branding, paths, packaging, and installation

The user explicitly asked to pause feature-porting and make the product identity consistent throughout the meaningful parts of the repository, especially configuration/data paths and the install layout for user-wide and system-wide installation. They also asked how this should eventually be installed on Penny's Arch Linux PC.

Treat this as the next main task. First perform a read-only audit, then propose and implement a cohesive plan in small, reviewable changes. Do not perform a blanket string replacement: upstream attribution, inherited Zen code/assets, license material, Mozilla identity, and upstream source references must remain correct where appropriate.

### Known branding inconsistencies to investigate

At last inspection on `security/librewolf-hardening`:
- `README.md` is still largely the upstream Zen README: heading says “Zen Browser,” Zen logos/badges/download/docs/release links and upstream contribution links remain. Rebrand it for LibreZen while retaining appropriate attribution and links to upstream projects.
- `package.json` still has `"name": "zen-desktop"`, an empty description/author, and repository, bugs, and homepage URLs pointing to `zen-browser/desktop`. Decide carefully which metadata should identify LibreZen and which should continue to point to upstreams.
- Some asset names and source references contain “Zen.” Inspect usage before renaming; inherited assets do not all need to be renamed.
- The WebGL documentation is now behind the latest runtime test results, as noted above.

Search for meaningful occurrences in places such as application/window names, about pages, branding resources, default preferences, program/executable names, app IDs, desktop launchers, icons, MIME handlers, update/release metadata, package scripts/manifests, installer destinations, profile/config/cache paths, and docs. Exclude vendored/upstream material from blanket replacements unless it is genuinely part of the end-user LibreZen identity.

### Paths and identity choices to evaluate

The user previously suggested keeping LibreZen's config/data separate from existing Zen Browser and LibreWolf installations, with `~/.config/LibreZen` as a tentative config path. Treat that as a preference to evaluate—not proof that the current browser/profile code already uses it, and not a decision to blindly relocate Firefox profile data.

Audit the existing profile/data path behavior and XDG handling first. Decide and document clear, consistent identities for:
- user-facing product and window name (`LibreZen` / `LibreZen Browser`, as appropriate);
- executable/launcher command (likely `librezen`);
- application ID / desktop-entry ID / icons and metadata;
- browser profile/data directory (keep isolated from Zen and LibreWolf);
- configuration, cache, and state paths;
- source/build directory versus installed program directory.

Do not rename the Firefox profile root to the config directory merely for branding if that breaks profile behavior or existing Mozilla conventions. Ensure paths that are code-sensitive, ABI/build-sensitive, or upstream-owned are changed only with evidence and tests.

### Arch Linux installation question

The user wants a practical future installation path for Penny's Arch Linux PC. This is **not solved yet**. Do not claim `npm run package` generates an Arch package until its output has been inspected.

Inspect the current Surfer package configuration and `npm run package` output, along with existing packaging scripts/manifests. Then recommend an install strategy that matches the actual artifacts:
- Native Arch packaging (for example, a maintained PKGBUILD/AUR-style route) if feasible and reproducible; and/or
- a self-contained release archive installed user-wide without root, and/or
- a system-wide installation option.

Keep build/source prerequisites distinct from end-user runtime/install prerequisites. Prefer an install/uninstall path with no root requirement for a user install; document the system-wide variant and exactly which files it owns. Plan desktop launcher and icon integration, app/profile isolation, upgrades, and uninstall behavior. Do not modify the machine's system install while doing the audit.

Potential conventional destinations to assess (not decisions until validated):
- User executable/launcher: `~/.local/bin/`
- User application files: `~/.local/opt/librezen/` or another clearly documented app directory
- User desktop entry/icons: `~/.local/share/applications/`, `~/.local/share/icons/`
- System application files: `/opt/librezen/` or a suitable `/usr/lib/` layout with a launcher under `/usr/bin/`
- System desktop entry/icons: `/usr/share/applications/`, `/usr/share/icons/`
- Tentative config path discussed: `~/.config/LibreZen/`; cache/state should follow a consistent XDG-compatible plan.
The correct layout depends on the runtime and package contents; don't impose these paths before inspecting how Firefox/Zen resolve profiles and resources.

### Suggested workflow for the next session

1. Read this handoff, then check local `git status`, `git branch --show-current`, and `git log -5 --oneline`. The remote repo received this handoff commit, so fetch/pull it before further edits if the local checkout is behind. Preserve unrelated working-tree changes.
2. Inspect relevant tracked configuration and build/package files, plus the full `README.md` and any existing branding/install files. Use targeted repository-wide search for likely branding, application ID, paths, and install strings.
3. Write a short inventory of current values versus proposed values, identifying occurrences that should intentionally remain upstream.
4. Decide the branding contract and profile/config/cache layout, then implement in small patches and test searches/build/runtime as practical.
5. Inspect `npm run package` output and implement/document a safe Arch install path. Verify both user-wide and system-wide file placement/removal where feasible.
6. Update the WebGL permission docs to reflect the already-confirmed tests without overstating the unchecked cases.

Ask the user before any destructive data migration or change that might touch existing Zen/LibreWolf profiles. Avoid unnecessary full rebuilds, and do not promise asynchronous follow-up; do the work in the active session.


## Results from the 2026-10-20 packaged-browser smoke test and identity pass

The packaged browser launched in a temporary HOME/profile and did not touch Penny's normal profile. First-run logs included missing initial Zen workspace/session database tables and a savedGroups session-startup error; those should be rechecked on a second launch rather than assumed harmless. Visiting https://get.webgl.org/ logged “WebGL is currently disabled”, so packaged-build WebGL acceptance remains unresolved even though a previous development-build run reportedly displayed the permission prompt.

The identity pass changes the project metadata and build configuration to LibreZen, while deliberately retaining the internal zen binary name until inherited packaging integrations are migrated. The tracked XDG path patch lowercases the application name, so librezen is the expected directory component, pending confirmation from a rebuilt package. The install destinations are documented in docs/branding-and-installation.md; do not migrate profiles.

The inherited release/AppImage/Flatpak automation still includes Zen-specific deployment assumptions. Do not use it to publish releases. Rebuild/repackage this revision and inspect application.ini before attempting any installation.


## Recovery note after the first branding rebuild attempt (2026-10-20)

The first rebuild attempt after commit badfac93 failed for two reasons:
- `configs/common/mozconfig` exported `MOZ_APP_VENDOR=LibreZen`, which this Firefox configure system rejects because the value is supplied as an implied option. Commit `672402988eb52b382fff2fec3192e62d8a5bac8e` removes that export and adds `src/browser/moz.configure.patch` to change the implied vendor value at its source. It also adds a reversible patch for the unofficial brand's `MOZ_APP_DISPLAYNAME`.
- The existing applied `aboutDialog-xhtml.patch` had been modified in place to change links. Surfer tries to reverse every tracked patch before reapplying it, so the modified patch no longer matched the already-patched file. The fix restores the original patch and moves the URL-only changes to `aboutDialog-z-brand-links.patch`.

Important: the attempted build failed in configure, and the subsequent `mach package` command ran anyway and reused the existing archive. The archive therefore still reported the old Zen name/vendor/source URL and is not validation of the new source.

For the next attempt, fetch the latest branch and run `npm run import` as a separate command. Do not run build/package unless import exits successfully. Fish's interactive `or return` is not a reliable way to abort a pasted command sequence at the prompt; run stages separately, or place the entire sequence in a Fish script that exits nonzero on failure. Do not run `surfer reset` or `npm run download -- --force` to work around this; those can delete the generated source/object directory and expensive build cache.
