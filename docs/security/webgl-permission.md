# LibreZen WebGL permission prompt

This patch ports LibreWolf's Firefox-158 WebGL permission flow into LibreZen's versioned Surfer patch set. Generated engine files are not edited directly.

Upstream references:
- LibreWolf WebGL engine patch: https://codeberg.org/librewolf/source/src/branch/main/patches/webgl-permission.patch
- LibreWolf permission UI integration: https://codeberg.org/librewolf/source/src/branch/main/patches/lw-permissions.patch
- LibreWolf settings documentation: https://librewolf.net/docs/settings/

The port includes an engine-side permission gate for HTML canvas and OffscreenCanvas/worker contexts, a browser-process prompt helper, per-origin allow/block decisions, session-only decisions in private windows, site-permission management, URL-bar indicator assets, English UI strings, and two static preferences.

## LibreZen defaults

- **librewolf.webgl.prompt = true**: a site must receive WebGL permission before its context can be created.
- **librewolf.webgl.prompt.hide = false**: show the prompt automatically for the initial LibreZen testing experience. Setting this to true switches to LibreWolf's quieter URL-bar-icon behavior.
- **webgl.disabled** remains the existing global WebGL switch. If it is enabled, WebGL is globally unavailable regardless of per-site decisions.

The visible-popup default is deliberate for LibreZen's first implementation and differs from LibreWolf's quieter default. The preference remains available through about:config.

## Validation status

The developer-build test previously reported by the user:
- npm run import applied the patch set successfully.
- npm run build completed successfully.
- Launching with npm start and visiting https://get.webgl.org/ reportedly showed the WebGL permission prompt. Session-only and remembered **Allow** choices were both tested.

The archive smoke test on 2026-10-20 launched the extracted browser in a temporary HOME and profile. However, when the test page was visited, its console logged **“WebGL is currently disabled”** and did not establish that the permission prompt worked in that packaged build. This may be a build/profile preference issue; it still needs to be isolated and retested after the LibreZen identity changes are rebuilt.

## Remaining acceptance tests

1. Confirm the prompt and both session-only and remembered decisions in a fresh profile in the packaged LibreZen build.
2. Test a remembered **Block** decision, remove/revoke that origin's permission under **Settings → Privacy & Security → Permissions → WebGL**, and verify the prompt returns.
3. Visit a second origin and verify its decision is independent.
4. Test a private window: the remember checkbox should be absent, and decisions should be session-only.
5. Try an OffscreenCanvas/WebGL worker test, if available.

Do not treat the previous development-build result as complete packaged-build validation; keep these remaining cases open until tested.
