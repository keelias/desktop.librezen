# LibreZen per-site JavaScript JIT permission

Status: implementation and patch-context checks are complete on the isolated feature branch; `npm run import`, compilation, and runtime behavior are still unverified.

## Intended behavior

- The site-identity panel contains an "Enable JavaScript JIT" toggle.
- The default is controlled by `librezen.jit.enabled-by-default` (true by default).
- A site override is stored as a `jit` permission against the effective site principal. Removing an override restores the default behavior instead of storing a redundant allow.
- Settings > Permissions includes a JavaScript JIT entry that opens the site-exceptions manager; saved allow/block entries can be reviewed and removed there.
- Process selection checks the effective top-level site for documents, subframes, and workers. This matters because JIT is selected when Gecko chooses a content-process type; toggling only a UI preference would not enforce the restriction.
- The change respects an existing enterprise-policy denial. After changing a site's permission, the current site is reloaded so it is recreated in the correct JIT-enabled or JIT-disabled process.
- The generated static-pref group is named `librezen`; new code should not introduce a new `librewolf.*` preference namespace.

## Validation required

The patch was checked against the pinned Firefox 158 source contexts and its overlapping hunks were checked against the existing WebGL permission patch. That is a static check only, not proof that Surfer will import it cleanly or that C++ will compile. Run `npm run import` and inspect every failed hunk before building. If import succeeds, run the existing full build, then test only using a temporary HOME and a disposable profile.

Check:
1. The toggle initially matches the default preference on a fresh site.
2. Disabling JIT reloads the page and leaves other sites unchanged.
3. The override survives a browser restart, appears in Settings > Permissions, and can be removed there. Toggling back to the default removes the site-specific override.
4. Changing `librezen.jit.enabled-by-default` in `about:config` changes the default for sites without an override.
5. A private window does not leak its site permission into the normal profile.
6. A WebAssembly-dependent page fails when JIT is disabled, while the normal page still works when JIT is enabled.
7. Check that changing permission reloads cleanly and does not cause repeated process swaps or console errors.

A graphical control for changing the global default is intentionally not included yet; for now, change `librezen.jit.enabled-by-default` in `about:config`. The per-site toggle and exception list should be validated before expanding the UI further.
