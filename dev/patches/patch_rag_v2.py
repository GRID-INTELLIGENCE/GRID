def patch_indexer():
    path = "e:/grid/tools/rag/indexer.py"
    with open(path, encoding="utf-8") as f:
        content = f.read()

    old_exclude = """            "research_snapshots", "archival", "ui_backup", "ui_node_modules_orphan",
            "Hogwarts", "visualizations"
        }"""

    new_exclude = """            "research_snapshots", "archival", "ui_backup", "ui_node_modules_orphan",
            "Hogwarts", "visualizations", "Arena", "datakit", "legacy_src"
        }"""

    content = content.replace(old_exclude, new_exclude)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched indexer.py with more excludes")


if __name__ == "__main__":
    patch_indexer()
