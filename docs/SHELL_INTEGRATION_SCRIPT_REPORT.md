# Shell Integration Script Integrity Report

Analysis of the Cursor/VS Code PowerShell shell integration script: integrity, safety, authenticity, and alignment with community guidelines. Use the hash and commands below to verify the script on your machine.

---

## 1. Script identity and hash

| Item | Value |
|------|--------|
| **Path** | `%LOCALAPPDATA%\Programs\cursor\resources\app\out\vs\workbench\contrib\terminal\common\scripts\shellIntegration.ps1` |
| **Origin** | Bundled with Cursor (VS Code–based); Microsoft copyright, MIT License |
| **SHA256** | `F2A02546D7A1A965FC8CFA9C47686245BC7D9C6948194A78F3BF397A9E378140` |

*Hash is for the file as installed; it may change after Cursor/VS Code updates.*

### Reproducibility (run from any shell)

```powershell
# PowerShell
Get-FileHash "c:\Users\USER\AppData\Local\Programs\cursor\resources\app\out\vs\workbench\contrib\terminal\common\scripts\shellIntegration.ps1" -Algorithm SHA256
```

```powershell
# Via cmd
cmd.exe /c "powershell -Command \"Get-FileHash 'c:\Users\USER\AppData\Local\Programs\cursor\resources\app\out\vs\workbench\contrib\terminal\common\scripts\shellIntegration.ps1' -Algorithm SHA256\""
```

```batch
certutil -hashfile "c:\Users\USER\AppData\Local\Programs\cursor\resources\app\out\vs\workbench\contrib\terminal\common\scripts\shellIntegration.ps1" SHA256
```

```bash
# WSL (path under /mnt/c)
sha256sum '/mnt/c/Users/USER/AppData/Local/Programs/cursor/resources/app/out/vs/workbench/contrib/terminal/common/scripts/shellIntegration.ps1'
```

---

## 2. Authenticity and integrity

- **Source**: Script lives under Cursor’s app resources (VS Code–based). Authenticity is established by the Cursor/VS Code installer and update mechanism, not by script-level signing.
- **Copyright**: Lines 1–4 contain Microsoft copyright and MIT License reference; behavior matches the [VS Code Terminal Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration) documentation.
- **Integrity**: Compare your file’s SHA256 to the hash above (and to the same path after updates). No in-repo signature verification; trust follows from the installed app.

---

## 3. Security assessment

### Legitimate and safe behavior

- **OSC 633**: Uses the documented VS Code escape sequences (A/B/C/D/E/P) for prompt, command, cwd, and properties; no use of untrusted input in sequences.
- **Environment**: Reads only `VSCODE_*` / `TERM_PROGRAM`-style variables set by the parent process; clears sensitive ones (e.g. `VSCODE_NONCE`) after use.
- **Nonce**: Command-line sequence (E) can include a nonce for spoofing prevention; optional and documented.
- **Language mode**: Exits immediately when `$ExecutionContext.SessionState.LanguageMode -ne "FullLanguage"` (e.g. ConstrainedLanguage), reducing risk in locked-down environments.
- **No dangerous patterns**: No `Invoke-Expression`, no execution of user-supplied strings, no network or file writes; env changes are from parent-supplied `VSCODE_ENV_REPLACE`/`PREPEND`/`APPEND` only.
- **Escaping**: `__VSCode-Escape-Value` escapes control characters and bytes 0x00–0x1F, `\`, newline, `;` for OSC output.

### Known issues and caveats

1. **Digital signature**: The script file is not Authenticode-signed (see e.g. VS Code issue #174021). In enterprises that require signed scripts, this can block execution or require policy exceptions.
2. **Execution policy**: Fails under `AllSigned` if the script itself is not signed. Common recommendation: `RemoteSigned` for general use; Bypass only for explicit one-off or scheduled runs.
3. **$Error pollution**: The script uses `Write-Error "failure" -ea ignore` to restore `$?`, which can append an entry to `$Error` (see [vscode#235298](https://github.com/microsoft/vscode/issues/235298)). Cosmetic/scripting concern, not a security vulnerability.
4. **Corporate tooling**: Some EDR or policy engines may flag unsigned, auto-injected scripts; document that this is the official Cursor/VS Code shell integration script.

---

## 4. Alignment with documentation and community practice

### VS Code docs

- Behavior matches the official [Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration) doc: OSC 633 A/B/C/D/E/P, nonce for E, Cwd/Prompt/HasRichCommandDetection/IsWindows, env reporting.
- Manual install guidance (profile snippet for pwsh) is consistent with the script’s expectations.

### Community best practices (summary)

| Practice | Script / environment |
|----------|----------------------|
| Execution policy | Script does not set policy; use `RemoteSigned` (or org policy). Avoid broad `Unrestricted`. |
| Code signing | Script is unsigned; enterprise may need exception or signed build. |
| Least privilege | Runs in user context; only modifies env and prompt/readline hooks. |
| No eval of untrusted input | No `Invoke-Expression` or similar on user/network data. |
| Logging/auditing | Not script’s role; handled by terminal/app. |

### Mismatches and clarifications

- **“OSC 7 fallback”**: Official VS Code shell integration is OSC 633; OSC 7 (cwd) is a separate, optional feature. The script correctly implements the documented 633 set; no “missing fallback” for OSC 7 in this script.
- **Cross-platform**: Script has Windows-specific branches (e.g. Windows 10 build check, `IsWindows`). This is documented and appropriate; “broader compatibility” in docs refers to multiple shells (bash, zsh, pwsh, etc.), not this single PowerShell script.

---

## 5. Safety and best-practices summary

| Dimension | Rating | Notes |
|-----------|--------|--------|
| **Integrity** | ✅ Verifiable | Use SHA256 above; re-check after updates. |
| **Authenticity** | ✅ Vendor | Microsoft-originated, shipped with Cursor/VS Code. |
| **Safety** | ✅ Good | No eval of untrusted input; restricted mode respected; env and escaping handled. |
| **Best-practices fit** | ⚠️ Partial | Unsigned; may conflict with AllSigned / enterprise policies. |
| **Overall** | **8/10** | Safe for typical use; enterprise and strict signing environments need policy or exceptions. |

---

## 6. Recommendations

1. **Verify after install/update**: Run `Get-FileHash ... -Algorithm SHA256` and compare to this document (and release notes if hashes are published).
2. **Execution policy**: Prefer `RemoteSigned` for interactive use; use `-ExecutionPolicy Bypass` only when explicitly invoking a specific script (e.g. diagnostics), not globally.
3. **Enterprise**: If your org requires signed scripts, request a signed build or an approved exception for this known Cursor/VS Code script; reference this report and the official VS Code shell integration docs.
4. **Monitoring**: Rely on Cursor/VS Code release notes and security advisories for shell integration changes; no separate feed for this single file.

---

## 7. References

- [VS Code – Terminal Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration)
- [VS Code issue #235298 – Shell integration and $Error](https://github.com/microsoft/vscode/issues/235298)
- [PowerShell execution policies (Microsoft Learn)](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies)
- [PowerShell vscode-powershell SECURITY.md](https://github.com/PowerShell/vscode-powershell/blob/HEAD/SECURITY.md) (reporting vulnerabilities)

---

*Report generated for GRID workspace; hash and path reflect a single Cursor installation. Update the hash section when verifying on another machine or after upgrading Cursor.*
