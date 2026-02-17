def patch_indexer():
    path = "e:/grid/tools/rag/indexer.py"
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Update defaults in function signatures
    content = content.replace("chunk_size: int = 2000", "chunk_size: int = 4000")
    content = content.replace("overlap: int = 200", "overlap: int = 400")
    content = content.replace("max_chunk_size: int = 1200", "max_chunk_size: int = 4000")

    # Update hardcoded val in update_index
    content = content.replace("chunk_size=2000, overlap=200", "chunk_size=4000, overlap=400")

    # Add more excludes
    old_exclude = """            "Hogwarts", "visualizations", "Arena", "datakit", "legacy_src"
        }"""

    new_exclude = """            "Hogwarts", "visualizations", "Arena", "datakit", "legacy_src",
            "artifacts", "analysis_report", "logs", "media", "assets", "temp"
        }"""

    content = content.replace(old_exclude, new_exclude)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched indexer.py with max limits and more excludes")


if __name__ == "__main__":
    patch_indexer()
