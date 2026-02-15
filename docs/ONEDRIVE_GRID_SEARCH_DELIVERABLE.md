# OneDrive GRID path search deliverable

## Script

**[e:\scripts\search_onedrive_grid_paths.ps1](e:\scripts\search_onedrive_grid_paths.ps1)** — searches OneDrive for files that reference:

- `E:\grid`, `E:/grid`
- `PROJECT_GRID`
- `grid-rag-enhanced`
- `E:\_projects`

File types: `.json`, `.env`, `.template`, `.md`, `.code-workspace`, `.yml`, `.yaml`.

## How to run

From PowerShell (may take a while on large OneDrive):

```powershell
E:\scripts\search_onedrive_grid_paths.ps1
```

## Interpretation

- **No matches:** Either no GRID path references exist in OneDrive, or they are in unsupported file types. Once the E:\grid junction exists, any correct `PROJECT_GRID=E:\grid` or `E:/grid` workspace paths resolve without change.
- **Matches:** List shows file path, line number, and line. For `.env`/`.env.editor`/templates, ensure `PROJECT_GRID=E:\grid`. For `.code-workspace`, ensure folder path is `E:/grid` or `E:\grid`. After the junction is in place, no edit is required unless the path was wrong. For docs/markdown, optionally add a note that E:\grid is a junction to `E:\_projects\grid-rag-enhanced` and repo is `caraxesthebloodwyrm02/GRID`.

## Status

E:\grid junction is in place. Configs under E:\ (OrganizedWorkspace.code-workspace, .env.editor.template, unified-server-configuration.json) already use E:\grid and resolve correctly. OneDrive search was not run to completion in automation (timeout); run the script manually if you need a full list under OneDrive.
