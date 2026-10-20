# Privacy and upstream services

**This is an engineering-status note, not a comprehensive legal privacy policy.** LibreZen is an experimental community fork, not an official Mozilla Firefox, Zen Browser, or LibreWolf release.

LibreZen combines inherited Zen Browser interface code, the Mozilla Firefox engine, and selected LibreWolf-derived privacy/security changes. As a result, network requests and data handling may depend on the exact source revision, browser preferences, search provider, enabled services, installed extensions, and visited sites. This project has not yet completed a full outbound-network audit of every inherited component, so it cannot responsibly promise that every upstream service is disabled or describe every possible data flow here.

Before distributing a public release, the project should document and test at least:
- telemetry, studies, crash reporting, and health-reporting preferences;
- safe-browsing, geolocation, search, translation, and other third-party service requests;
- update checks and the absence or presence of a LibreZen-operated update service;
- extension permissions and browser profile storage.

No independent LibreZen update service or account/sync service is documented as available at this stage. Do not assume automatic updates are configured merely because a package or update manifest can be generated.

For upstream-specific information, consult the privacy documentation published by [Mozilla](https://www.mozilla.org/privacy/), [Zen Browser](https://zen-browser.app/privacy-policy/), and [LibreWolf](https://librewolf.net/). Those policies describe their respective projects and should not be read as a complete policy for LibreZen.

If you discover a privacy-sensitive issue in LibreZen itself, report it privately using the instructions in SECURITY.md.
