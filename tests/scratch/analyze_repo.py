import os
from pathlib import Path


def analyze_repo(repo_path):
    repo = Path(repo_path)
    dir_stats = {}

    exclude_dirs = {
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        ".venv",
        "venv",
        ".env",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".tox",
        ".rag_db",
        ".rag_logs",
        "research_snapshots",
        "archival",
        "ui_backup",
        "ui_node_modules_orphan",
        "Hogwarts",
        "visualizations",
        "Arena",
        "datakit",
        "legacy_src",
    }

    file_count = 0
    total_size = 0

    for root, dirs, files in os.walk(repo):
        # Apply same exclusion logic as indexer
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        rel_root = Path(root).relative_to(repo)
        top_dir = rel_root.parts[0] if rel_root.parts else "."

        if top_dir not in dir_stats:
            dir_stats[top_dir] = {"files": 0, "size": 0}

        for f in files:
            p = Path(root) / f
            try:
                sz = p.stat().st_size
                dir_stats[top_dir]["files"] += 1
                dir_stats[top_dir]["size"] += sz
                file_count += 1
                total_size += sz
            except Exception:
                pass

    print(f"Total Files: {file_count}")
    print(f"Total Size: {total_size / (1024*1024):.2f} MB")
    print("\nTop Directories by file count:")
    sorted_stats = sorted(dir_stats.items(), key=lambda x: x[1]["files"], reverse=True)
    for d, s in sorted_stats[:20]:
        print(f"{d:30} : {s['files']:6} files, {s['size']/(1024*1024):7.2f} MB")


if __name__ == "__main__":
    analyze_repo(".")
