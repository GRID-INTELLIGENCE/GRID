

def patch_indexer():
    path = "e:/grid/tools/rag/indexer.py"
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Update defaults in function signatures
    content = content.replace("chunk_size: int = 6000", "chunk_size: int = 3000")
    content = content.replace("overlap: int = 600", "overlap: int = 300")
    content = content.replace("max_chunk_size: int = 6000", "max_chunk_size: int = 3000")

    # Update hardcoded val in update_index
    content = content.replace("chunk_size=6000, overlap=600", "chunk_size=3000, overlap=300")

    # Update warning limit
    content = content.replace("> 4000", "> 3000")
    content = content.replace("(4000 chars)", "(3000 chars)")

    # Add more excludes
    old_exclude = """            "artifacts", "analysis_report", "logs", "media", "assets", "temp"
        }"""

    new_exclude = """            "artifacts", "analysis_report", "logs", "media", "assets", "temp",
            "rust", "interfaces", "acoustics", "awareness", "evolution", "motion"
        }"""

    content = content.replace(old_exclude, new_exclude)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched indexer.py with 3000 char limits and more excludes")


if __name__ == "__main__":
    patch_indexer()
