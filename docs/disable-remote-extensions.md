# Disabling Remote Development & remote extensions in this workspace

This workspace is configured to avoid VS Code Remote Development features and prevent key Remote Development extensions from running on remote extension hosts. The change is done at the *workspace settings* level to avoid blacklisting or removing extensions.

What the workspace settings do:

Files/keys updated:
  - `remote.extensionKind` mapping for: `ms-vscode-remote.remote-ssh`, `ms-vscode-remote.remote-ssh-edit`, `ms-vscode-remote.remote-containers`, `ms-vscode-remote.remote-wsl`, `ms-vscode-remote.remote-tunnels` (all forced to `"ui"`).
  - `remote.restoreForwardedPorts`: false
  - `remote.SSH.defaultExtensions`, `dev.containers.defaultExtensions`, `remote.tunnels.defaultExtensions`: []
  - `remote.SSH.showLoginTerminal`: false
  - `remote.SSH.useLocalServer`: false

Why this approach?

How to revert:
1. Open `.vscode/settings.json` and remove the `remote.*` keys you want to restore.
2. If you want remote extensions to run remotely again, delete the entries in `remote.extensionKind` or set them to `"workspace"`.

If you want a stricter policy (e.g., prevent _all_ remote extension activation no matter the extension IDs), that is not possible with a single wildcard setting — we can add per-extension `remote.extensionKind` entries for the full list of IDs you expect in your environment. Tell me if you'd like me to make a more aggressive coverage list.

Telemetry / proxy / certificate changes

In addition to forcing remote extension hosts to run locally, the workspace settings now also disable telemetry and reduce proxy/certificate usage for this workspace. The keys added accomplish the following:

- `telemetry.enableTelemetry`: false — turn off telemetry in this workspace.
- `telemetry.telemetryLevel`: "off" — explicit telemetry level off.
- `telemetry.feedback.enabled`: false — disable feedback prompts.
- `http.proxySupport`: "off" — do not use proxy support in this workspace.
- `http.proxy` / `http.noProxy`: cleared to avoid using workspace-level proxy.
- `http.proxyStrictSSL`: false — avoid strict SSL proxy checks.
- `http.useLocalProxyConfiguration`: false — do not use local proxy configuration from the environment.
- `http.systemCertificates` / `http.systemCertificatesNode` / `http.experimental.systemCertificatesV2`: false — avoid relying on OS-provided certificate plumbing in this workspace.

Revert or tweak

1. Remove or edit the keys in `.vscode/settings.json` to restore a given behavior.
2. If you want to allow a proxy only for this workspace, set `http.proxy` to the desired proxy URI and `http.proxySupport` to `on`.
3. If an enterprise policy governs `extensions.allowed` or other system-level settings, those need to be changed by whoever manages your policy server — workspace settings can't override device management policies.

If you'd like I can also add a small workspace verification (CI check or dev script) that optionally asserts the presence of these workspace settings.
