# LibreZen

**LibreZen is an experimental browser project combining Zen Browser's interface with Firefox and selected LibreWolf-inspired privacy and security hardening.** It is an independent fork, not an official release of Zen Browser or LibreWolf.

> [!WARNING]
> LibreZen currently requires a source build. A tested end-user installer, package-manager package, and upgrade/uninstall workflow are not available yet. Do not treat the development build instructions below as installation instructions.

## Project status

- **Base:** Zen Browser UI on Firefox.
- **Security work:** selected LibreWolf patches are ported into LibreZen's versioned patch set.
- **Verified feature:** the WebGL permission prompt has been built and manually tested, including both session-only and remembered site permissions.
- **Build environment:** use the runtime versions pinned in .nvmrc, .python-version, and .rust-toolchain. The current tested setup uses Node.js 22, Python 3.11, and Rust 1.95.
- **Installation:** packaging and LibreZen-specific application/profile identity are still being audited. See [Branding and installation plan](docs/branding-and-installation.md).

## Build and run from source

These commands are for development, not a system installation. Run them from a clean checkout after installing the required system dependencies described by the upstream build documentation.

```sh
npm ci
npm run init
npm run build
npm start
```

The first initialization and build can take a long time and download/build a large toolchain. On Linux, use a supported distribution with the build dependencies required by Firefox/Zen. The repository's build scripts and configuration are still being adapted for LibreZen.

## Security documentation

- [WebGL permission prompt port and manual acceptance checklist](docs/security/webgl-permission.md)
- [Branding, application identity, paths, and installation plan](docs/branding-and-installation.md)

## Upstream projects and attribution

LibreZen builds on the work of the [Zen Browser](https://github.com/zen-browser/desktop) and [Firefox](https://www.mozilla.org/firefox/) projects, and ports selected security changes from [LibreWolf](https://codeberg.org/librewolf). Their source code, assets, licenses, and notices remain subject to their respective upstream terms. See [LICENSE](LICENSE) and the notices distributed with the relevant source files.

## Contributing

Please keep changes reproducible: make persistent engine changes through the repository's source patches/configuration rather than editing the generated engine/ tree directly. For security-sensitive changes, document upstream provenance and provide a manual or automated acceptance test where practical.

LibreZen is experimental. Security features and browser integration should be considered individually tested only when their stated tests have actually passed.
