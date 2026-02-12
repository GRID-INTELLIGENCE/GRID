# Embedding Generation Quick Start Guide

## Your System Profile
- **CPU:** AMD Ryzen 7 7700 (16 logical cores @ 3.8 GHz)
- **RAM:** 32 GB
- **GPU:** AMD Radeon (512 MB) - **NOT suitable for GPU acceleration**
- **Recommendation:** CPU-based embedding with aggressive batching

---

## Quick Setup

### 1. Install Required Libraries
```bash
pip install sentence-transformers torch psutil
```

### 2. Using the Optimized Script
```bash
# Basic usage
python e:\generate_embeddings_optimized.py input.json output.json

# With custom batch size (recommended: 256-512)
python e:\generate_embeddings_optimized.py input.json output.json --batch-size 512

# With INT8 quantization (save ~50% memory, +20% speed)
python e:\generate_embeddings_optimized.py input.json output.json --quantize

# Using a different model (nomic-embed-text-v1.5 recommended)
python e:\generate_embeddings_optimized.py input.json output.json --model nomic-embed-text-v1.5
```

### 3. Input File Format
```json
[
  {"id": "1", "text": "Your first document here..."},
  {"id": "2", "text": "Your second document here..."},
  {"id": "3", "text": "Your third document here..."}
]
```

Or JSONL format:
```
{"id": "1", "text": "First document..."}
{"id": "2", "text": "Second document..."}
{"id": "3", "text": "Third document..."}
```

---

## Performance Comparison

### Model Options

| Model | Size | Speed (texts/sec) | Memory per 256 batch | Recommended |
|-------|------|-------------------|---------------------|-------------|
| **all-MiniLM-L6-v2** | 22 MB | ~400 | ~1 GB | ✅ BEST |
| **all-mpnet-base-v2** | 428 MB | ~250 | ~2 GB | Good |
| **nomic-embed-text-v1.5** | 137 MB | ~300 | ~1.5 GB | ✅ Good balance |

### Batch Size Impact
```
Batch 64:   ~150 texts/sec, ~0.5 GB memory
Batch 128:  ~250 texts/sec, ~1 GB memory
Batch 256:  ~350 texts/sec, ~2 GB memory    ← RECOMMENDED
Batch 512:  ~400 texts/sec, ~4 GB memory    (if text is short)
```

---

## Optimization Techniques (Ranked by Impact)

### ⚡ IMMEDIATE WINS (Do These First)

**1. Set Thread Count**
```bash
# Windows PowerShell
$env:OMP_NUM_THREADS = '8'
$env:MKL_NUM_THREADS = '8'

# Then run your Python script
python generate_embeddings_optimized.py ...
```

**2. Use Small Model**
```bash
# Instead of large models, use:
python generate_embeddings_optimized.py data.json output.json \
  --model all-MiniLM-L6-v2
```

**3. Aggressive Batching**
```bash
# Use batch size 256 or 512
python generate_embeddings_optimized.py data.json output.json \
  --batch-size 512
```

### ⚡⚡ MEDIUM IMPACT

**4. Enable Quantization**
```bash
python generate_embeddings_optimized.py data.json output.json --quantize
# ~20% faster, ~50% less memory
```

**5. Stream Large Files**
```python
# For files > 1GB, process in chunks:
def process_large_file(file_path, chunk_size=10000):
    with open(file_path, 'r') as f:
        chunk = []
        for line in f:
            chunk.append(json.loads(line))
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk
```

### ⚡⚡⚡ ADVANCED

**6. Cache Embeddings**
```python
import pickle

def get_cached_embeddings(texts, cache_file='embedding_cache.pkl'):
    cache = {}
    if Path(cache_file).exists():
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
    
    uncached = [t for t in set(texts) if t not in cache]
    if uncached:
        embeddings = model.encode(uncached, batch_size=256)
        cache.update(dict(zip(uncached, embeddings)))
        
        with open(cache_file, 'wb') as f:
            pickle.dump(cache, f)
    
    return [cache[t] for t in texts]
```

**7. Parallel I/O with Threading**
```python
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

def parallel_embedding_pipeline(texts, model):
    batch_size = 256
    num_workers = 4
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        
        # Submit batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            future = executor.submit(model.encode, batch, batch_size=256)
            futures.append(future)
        
        # Collect results
        results = []
        for future in futures:
            results.extend(future.result())
    
    return results
```

---

## Troubleshooting

### Problem: "Out of Memory"
**Solution 1:** Reduce batch size
```bash
python generate_embeddings_optimized.py data.json output.json --batch-size 128
```

**Solution 2:** Use smaller model
```bash
python generate_embeddings_optimized.py data.json output.json \
  --model all-MiniLM-L6-v2
```

**Solution 3:** Process in chunks
```python
texts_per_batch = 50000
for i in range(0, len(all_texts), texts_per_batch):
    batch = all_texts[i:i+texts_per_batch]
    embeddings = model.encode(batch, batch_size=256)
    save_batch(embeddings, f"batch_{i}.json")
```

### Problem: "CPU is at 100% but slow"
**Solution:** Already at optimal CPU usage!
- This is normal and expected
- Consider splitting workload across multiple Python processes

### Problem: "Disk I/O bottleneck"
**Solution:** Write to SSD, use JSONL format (faster parsing)
```python
# Save as JSONL instead of JSON
with open('output.jsonl', 'w') as f:
    for emb_data in embeddings:
        f.write(json.dumps(emb_data) + '\n')
```

### Problem: "Model download is slow"
**Solution:** Pre-download or cache models
```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; \
  SentenceTransformer('all-MiniLM-L6-v2')"

# Models cached in: %USERPROFILE%\.cache\huggingface\hub\
```

---

## Monitoring Performance

### Check Memory Usage
```python
import psutil
import os

process = psutil.Process(os.getpid())
mem = process.memory_info().rss / 1024**3
print(f"Current memory: {mem:.2f} GB / 32 GB")
```

### Profile Speed
```python
import time

start = time.time()
embeddings = model.encode(texts, batch_size=256)
elapsed = time.time() - start

print(f"Speed: {len(texts) / elapsed:.0f} texts/second")
```

### Monitor CPU Threads
```bash
# Windows PowerShell
Get-Process python | Select-Object ProcessorAffinity
```

---

## Recommended Configuration for Your System

```python
# optimal_config.py
from sentence_transformers import SentenceTransformer
import os

# Set threads
os.environ['OMP_NUM_THREADS'] = '8'
os.environ['MKL_NUM_THREADS'] = '8'

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')
model = model.cpu()

# Encode with optimal batch size
embeddings = model.encode(
    texts,
    batch_size=256,  # Perfect balance for your system
    show_progress_bar=True,
    convert_to_numpy=False
)

# Expected results:
# - Speed: 350-450 texts/second
# - Memory: 2-4 GB peak
# - For 1M embeddings: ~40-50 minutes
```

---

## For Very Large Datasets (>100M texts)

Use a vector database to avoid storing all embeddings in RAM:

```bash
# Install Chroma (local vector DB)
pip install chromadb

# Create embeddings and store directly
python -c "
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

settings = Settings(
    chroma_db_impl='duckdb',
    anonymized_telemetry=False
)

client = chromadb.Client(settings)
collection = client.create_collection(name='my_embeddings')

model = SentenceTransformer('all-MiniLM-L6-v2')

# Process in batches and store directly
for i in range(0, len(texts), 10000):
    batch = texts[i:i+10000]
    embeddings = model.encode(batch, batch_size=256)
    
    collection.add(
        ids=[f'doc_{j}' for j in range(i, i+len(batch))],
        embeddings=embeddings,
        documents=batch
    )
    
    print(f'Stored {i+len(batch)} embeddings')
"
```

---

## Expected Performance Benchmarks

Based on your Ryzen 7700 + 32GB RAM:

| Task | Time | Notes |
|------|------|-------|
| 10k texts (avg 100 words) | ~30 sec | Batch 256 |
| 100k texts | ~5 min | All in memory |
| 1M texts | ~45 min | All in memory |
| 10M texts | ~7.5 hours | Streaming required |

**Recommendation:** Use vector database (Chroma) for >100M texts

---

## Next Steps

1. **Install:** `pip install sentence-transformers torch psutil`
2. **Test:** `python e:\generate_embeddings_optimized.py --help`
3. **Run:** `python e:\generate_embeddings_optimized.py your_data.json output.json`
4. **Monitor:** Check output stats for your actual performance
5. **Optimize:** Adjust batch size based on memory available

---

## Additional Resources

- [Sentence Transformers Docs](https://www.sbert.net/)
- [HuggingFace Model Hub](https://huggingface.co/models)
- [ChromaDB for Vector Storage](https://docs.trychroma.com/)
- [PyTorch Optimization Guide](https://pytorch.org/docs/stable/notes/amp_examples.html)
