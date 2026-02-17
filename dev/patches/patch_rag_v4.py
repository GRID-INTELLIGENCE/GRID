def patch_indexer():
    path = "e:/grid/tools/rag/indexer.py"
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Update defaults in function signatures
    content = content.replace("chunk_size: int = 4000", "chunk_size: int = 6000")
    content = content.replace("overlap: int = 400", "overlap: int = 600")
    content = content.replace("max_chunk_size: int = 4000", "max_chunk_size: int = 6000")

    # Update hardcoded val in update_index
    content = content.replace("chunk_size=4000, overlap=400", "chunk_size=6000, overlap=600")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched indexer.py with 6000 char limits")


if __name__ == "__main__":
    patch_indexer()
