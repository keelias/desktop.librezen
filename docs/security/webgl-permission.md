# LibreZen WebGL permission prompt

This patch ports LibreWolf's Firefox-158 WebGL permission flow into LibreZen's versioned Surfer patch set. Generated `engine/` files are not edited directly.

Upstream references:
- LibreWolf WebGL engine patch: https://codeberg.org/librewolf/source/src/branch/main/patches/webgl-permission.patch
- LibreWolf permission UI integration: https://codeberg.org/librewolf/source/src/branch/main/patches/lw-permissions.patch
- LibreWolf settings documentation: https://librewolf.net/docs/settings/

The port includes the engine-side permission gate for HTML canvas and OffscreenCanvas/worker contexts, the browser-process prompt helper, per-origin allow/block decisions, session-only decisions in private windows, site-permission management, URL-bar indicator assets, English UI strings, and the two static preferences.

## LibreZen defaults

- `librewolf.webgl.prompt = true`: a site must receive WebGL permission before its context can be created.
- `librewolf.webgl.prompt.hide = false`: show the prompt automatically for the initial LibreZen testing experience. Setting this to `true` switches to LibreWolf's quieter URL-bar-icon behavior.
- `webgl.disabled` remains the existing global WebGL switch. If it is enabled, WebGL is globally unavailable regardless of per-site decisions.

The visible-popup default is deliberate for LibreZen's first implementation and differs from LibreWolf's quieter default. The preference remains available through `about:config`.

## Manual acceptance checklist

1. Use a fresh profile or remove any saved WebGL permission for the test origin. Open a page that creates a WebGL context, such as https://get.webgl.org/. The permission popup should appear before the context is granted.
2. Choose **Block** with “Remember this decision” checked. Reload and revisit the site; it should remain blocked without granting a context.
3. Remove that origin from **Settings → Privacy & Security → Permissions → WebGL**, revisit it, and confirm the request appears again.
4. Choose **Allow** with “Remember this decision” checked. The browser should reload the tab and the page should be able to create its WebGL context.
5. Visit a second origin and verify that the first origin's decision is not automatically reused.
6. Test a private window. The remember checkbox should be absent, and the decision should be session-only.
7. Try a site that uses OffscreenCanvas/WebGL in a worker, if available, to check that the non-main-thread path remains covered.

Until a built LibreZen binary has been tested, these are expected behaviors, not a claim that the port has passed runtime testing.
