# Windows Options to Restore Backed-Up Files and Folders

Reference for all Windows-related ways to restore files and folders. For Grid directory and commit restore, see [RESTORE.md](RESTORE.md) and [d:\Build\GRID-main\COMMIT_RESTORATION.md](d:\Build\GRID-main\COMMIT_RESTORATION.md).

---

## 1. File and folder restore (user data)

| Option | What it restores | How to access / use |
|--------|------------------|----------------------|
| **Recycle Bin** | Files/folders deleted locally and not yet emptied | Open Recycle Bin, right-click item, **Restore**. Restores to original location. |
| **File History** | Previous versions of files in user libraries (Desktop, Documents, Pictures, etc.) backed up to external drive or network | **Settings > Update & Security > Backup** (Win10) or **Settings > Accounts > Windows Backup** (Win11); or **Control Panel > File History > Restore personal files**; or in File Explorer: **Home** tab > **History**; or right-click file/folder > **Restore previous versions**. |
| **Previous Versions (Properties)** | Versions from File History or from System Restore / shadow copies | Right-click file or folder > **Properties** > **Previous Versions** tab. Select a version, then **Open** (preview), **Restore** (overwrite), or **Copy** (to another location). |
| **OneDrive** | Files in OneDrive folder: recycle bin and version history | OneDrive folder: **Recycle bin** (online or sync); or right-click file > **Version history** in OneDrive. [Restore deleted files from OneDrive](https://support.microsoft.com/en-us/topic/09754559-adba-4b7f-b1f1-cc85c06d47d5). |
| **Windows Backup (cloud)** | Files, settings, apps backed up via Microsoft account (OneDrive-linked folders) | Restore when setting up a new PC (sign in with same Microsoft account) or via OneDrive/backup settings. [Back up and restore with Windows Backup](https://support.microsoft.com/en-us/windows/back-up-and-restore-with-windows-backup-87a81f8a-78fa-456e-b521-ac0560e32338). |
| **Backup and Restore (Windows 7)** | Legacy full or selective backups to external/media | **Control Panel > Backup and Restore (Windows 7)**. **Restore my files** to browse and restore from backup. Still available in Windows 10/11. |
| **Shadow copies (VSS)** | Volume shadow copies created by System Protection or other VSS writers | Shown in **Previous Versions** tab (same as above). Or use **System Restore** to restore the whole volume state (see below). |
| **External / manual backup** | Any folder you copied to USB, external drive, or network | Copy back from the backup location; no built-in UI beyond File Explorer. |

---

## 2. System-level recovery (can affect files and folders)

| Option | What it restores | How to access |
|--------|------------------|----------------|
| **System Restore** | System files, registry, installed programs to a restore point; personal files usually kept | **Settings > System > Recovery** or run `rstrui.exe`. Choose a restore point. [System Restore](https://support.microsoft.com/en-us/windows/system-restore-a5ae3ed9-07c4-fd56-45ee-096777ecd14e). |
| **System Protection (restore points)** | Same as System Restore; also feeds **Previous Versions** for some locations | **Control Panel > System > System protection** to configure; restore via System Restore. [System Protection](https://support.microsoft.com/en-us/windows/system-protection-e9126e6e-fa64-4f5f-874d-9db90e57645a). |
| **Reset this PC** | Reinstall Windows; optional "keep my files" or "remove everything" | **Settings > System > Recovery > Reset this PC**. [Reset your PC](https://support.microsoft.com/en-us/windows/recovery-options-in-windows-31ce2444-7de3-818c-d626-e3b5a3024da5). |
| **Recovery Drive** | Bootable USB to access Windows RE; does not back up personal files | Create: **Control Panel > Create a recovery drive**. Use to boot and run System Restore, System Image Recovery, etc. [Recovery Drive](https://support.microsoft.com/en-us/windows/recovery-drive-abb4691b-5324-6d4a-8766-73fab304c246). |
| **Windows Recovery Environment (WinRE)** | Startup Repair, System Restore, System Image Recovery, Command Prompt, Reset | Triggered when Windows fails to start, or **Settings > Recovery > Advanced startup**. [Windows Recovery Environment](https://support.microsoft.com/en-us/windows/windows-recovery-environment-0eb14733-6301-41cb-8d26-06a12b42770b). |
| **System Image Recovery** | Full volume restore from a system image (created via Backup and Restore or other tools) | From Windows RE or **Control Panel > Backup and Restore (Windows 7) > Restore system settings or your computer > Advanced recovery methods**. |
| **PC-to-PC transfer** | Move files/settings from an old Windows PC to a new one | **Settings** or "Transfer to new PC" flows; can use OneDrive, external storage, or Backup and Restore from Windows 7/8.1. [Transfer to a new PC](https://support.microsoft.com/en-us/windows/transfer-your-files-and-settings-to-a-new-windows-pc-57b8d163-d80e-44fe-8247-62f7cf84a8ed). |

**Overview:** [Backup, restore, and recovery in Windows](https://support.microsoft.com/en-us/windows/backup-restore-and-recovery-in-windows-e6d629c4-2568-4406-814f-209a2af06ef7).

---

## 3. Summary: restore my files/folders only

For **files and folders** (e.g. Grid directory, user_context):

1. **Recycle Bin** — if just deleted and not emptied.
2. **Previous Versions** (right-click > Properties > Previous Versions) — uses File History and/or shadow copies.
3. **File History** — if enabled and backup drive is connected; restore via Control Panel or File Explorer **History**.
4. **OneDrive** — if the folder is under OneDrive; version history and Recycle Bin.
5. **Windows Backup / OneDrive backup** — if you use Microsoft account backup; restore on same or new PC.
6. **Backup and Restore (Windows 7)** — if you have a legacy backup; **Restore my files**.
7. **External/manual copy** — copy back from USB, external drive, or network share.
8. **System Restore** — only if you need the whole drive state; use with care (can affect apps/settings).
