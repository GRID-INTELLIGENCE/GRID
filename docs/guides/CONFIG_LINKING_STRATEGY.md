# Configuration Linking Strategy (C ↔ E Drive)

## Overview
This document describes how user settings (C: drive) and workspace settings (E: drive) are linked and coordinated for optimal functionality.

## Configuration Hierarchy

```
1. User Settings (C:\Users\irfan\AppData\Roaming\Cursor\User\settings.json)
   ├─ Base configuration for all workspaces
   ├─ Font: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', Consolas
   ├─ Font Size: 16
   ├─ Theme: Default Dark Modern
   └─ Performance optimizations

2. Workspace Settings (E:\Apps\.vscode\settings.json)
   ├─ Inherits from User Settings
   ├─ Adds TypeScript-specific configurations
   └─ Path mappings for cross-drive resolution

3. Project Settings (E:\Apps\data-viz-studio\tsconfig.json)
   ├─ Extends base TypeScript configuration
   ├─ Project-specific paths and includes
   └─ References tsconfig.node.json for build tools
```

## Linking Mechanisms

### 1. TypeScript Configuration
- Parent config: `E:\Apps\tsconfig.json` (base configuration)
- Project configs: Individual `tsconfig.json` files reference parent via project references
- Path resolution: Uses `baseUrl` and `paths` to resolve across drives

### 2. Python Configuration
- User settings define base Python paths
- Workspace settings add project-specific paths using `${workspaceFolder}`
- Terminal environment variables bridge C and E drives

### 3. Settings Inheritance
- Workspace settings (`E:\Apps\.vscode\settings.json`) complement user settings
- Conflicts: Workspace settings override user settings
- Shared settings: Both locations maintain consistency for font, theme, etc.

### 4. Performance Optimization
- Warmup config (`C:\Users\irfan\.cursor\warmup-config.json`) defines startup strategy
- File watcher exclusions optimized for large workspaces
- Language server memory allocations shared across drives

## File System Links (if needed)

To create symbolic links for shared configurations:
```powershell
# Example: Link shared config directory
New-Item -ItemType SymbolicLink -Path "E:\Apps\shared-config" -Target "C:\Users\irfan\.cursor\shared"
```

## Validation Checklist

- [x] User settings standardized (font, theme, performance)
- [x] Workspace settings inherit properly
- [x] TypeScript path resolution works across drives
- [x] Python paths configured correctly
- [x] File watcher exclusions optimized
- [x] Performance settings aligned
- [x] Extension recommendations synchronized

## Troubleshooting

If settings don't apply:
1. Check workspace settings override user settings correctly
2. Verify TypeScript project references are valid
3. Ensure file paths use proper drive letters (C: vs E:)
4. Restart Cursor after configuration changes
5. Check for JSON syntax errors in config files
