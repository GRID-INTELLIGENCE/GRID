#!/usr/bin/env python3
"""
Optimized embedding generation script for your system
Usage: python generate_embeddings.py <input_file> <output_file> [--model MODEL] [--batch-size BATCH]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

import psutil

# Set thread environment variables BEFORE importing heavy libraries
os.environ["OMP_NUM_THREADS"] = "8"
os.environ["MKL_NUM_THREADS"] = "8"
os.environ["OPENBLAS_NUM_THREADS"] = "8"

try:
    import torch

    torch.set_num_threads(8)
except ImportError:
    print("PyTorch not installed. Installing...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "torch"])
    import torch

    torch.set_num_threads(8)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Sentence Transformers not installed. Installing...")
    import subprocess

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "sentence-transformers"]
    )
    from sentence_transformers import SentenceTransformer


class OptimizedEmbeddingGenerator:
    """Generate embeddings optimized for your system specs"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 256,
        device: str = "cpu",
        quantize: bool = False,
    ):
        """
        Initialize embedding generator

        Args:
            model_name: HuggingFace model identifier
            batch_size: Batch size for processing (256 recommended for your system)
            device: 'cpu' or 'cuda' (GPU not recommended for your system)
            quantize: Apply INT8 quantization (experimental)
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.quantize = quantize

        print(f"Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)

        if device == "cpu":
            self.model = self.model.cpu()

        if quantize and device == "cpu":
            print("Applying INT8 quantization...")
            try:
                # Apply quantization to the model
                self.model = torch.quantization.quantize_dynamic(
                    self.model, {torch.nn.Linear}, dtype=torch.qint8
                )
            except Exception as e:
                print(f"Quantization failed: {e}")

        self.model.eval()  # Set to evaluation mode
        print(f"Model loaded successfully | Device: {device}")

    def get_system_memory_mb(self) -> float:
        """Get current process memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def embed_texts(
        self, texts: List[str], show_progress: bool = True
    ) -> Tuple[List[List[float]], dict]:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar

        Returns:
            Tuple of (embeddings, metadata)
        """
        stats = {
            "total_texts": len(texts),
            "start_memory_mb": self.get_system_memory_mb(),
            "start_time": time.time(),
            "batches_processed": 0,
        }

        print(f"\nGenerating embeddings for {len(texts)} texts...")
        print(f"Batch size: {self.batch_size}")
        print(f"Initial memory: {stats['start_memory_mb']:.1f} MB")

        # Generate embeddings with progress bar
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            device=self.device,
        )

        # Convert numpy array to list of lists
        if hasattr(embeddings, 'tolist'):
            embeddings = embeddings.tolist()
        else:
            embeddings = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]

        # Calculate stats
        stats["end_time"] = time.time()
        stats["end_memory_mb"] = self.get_system_memory_mb()
        stats["elapsed_seconds"] = stats["end_time"] - stats["start_time"]
        stats["memory_delta_mb"] = stats["end_memory_mb"] - stats["start_memory_mb"]
        stats["texts_per_second"] = len(texts) / stats["elapsed_seconds"]

        return embeddings, stats

    def embed_from_file(
        self,
        input_file: str,
        output_file: str,
        text_key: str = "text",
        id_key: str = "id",
    ) -> dict:
        """
        Load texts from JSON file and generate embeddings

        Args:
            input_file: Path to JSON file with texts
            output_file: Path to save embeddings
            text_key: JSON key containing text
            id_key: JSON key containing document ID

        Returns:
            Processing statistics
        """
        # Load input file
        print(f"Loading texts from: {input_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            if input_file.endswith(".jsonl"):
                data = [json.loads(line) for line in f]
            else:
                data = json.load(f)

        texts = [item[text_key] for item in data]
        ids = [item.get(id_key, i) for i, item in enumerate(data)]

        print(f"Loaded {len(texts)} texts")

        # Generate embeddings
        embeddings, stats = self.embed_texts(texts)

        # Save results
        print(f"\nSaving embeddings to: {output_file}")
        output_data = [
            {
                id_key: doc_id,
                "embedding": emb,
                text_key: text,
            }
            for doc_id, emb, text in zip(ids, embeddings, texts)
        ]

        with open(output_file, "w", encoding="utf-8") as f:
            if output_file.endswith(".jsonl"):
                for item in output_data:
                    f.write(json.dumps(item) + "\n")
            else:
                json.dump(output_data, f, indent=2)

        # Print statistics
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Total texts processed:  {stats['total_texts']}")
        print(f"Time elapsed:           {stats['elapsed_seconds']:.2f} seconds")
        print(f"Throughput:             {stats['texts_per_second']:.0f} texts/second")
        print(f"Memory start:           {stats['start_memory_mb']:.1f} MB")
        print(f"Memory end:             {stats['end_memory_mb']:.1f} MB")
        print(f"Memory delta:           {stats['memory_delta_mb']:.1f} MB")
        print(f"Output file:            {output_file}")
        print("=" * 60)

        return stats


def main():
    parser = argparse.ArgumentParser(
        description="Generate optimized embeddings for your system (Ryzen 7700, 32GB RAM)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_embeddings.py texts.json embeddings.json
  python generate_embeddings.py texts.jsonl embeddings.jsonl --model all-mpnet-base-v2 --batch-size 512
  python generate_embeddings.py texts.json embeddings.json --quantize
        """,
    )

    parser.add_argument("input_file", help="Input JSON/JSONL file with texts")
    parser.add_argument("output_file", help="Output file for embeddings")
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="HuggingFace model (default: all-MiniLM-L6-v2)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=256,
        help="Batch size for processing (default: 256, try 512 for your system)",
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        help="Apply INT8 quantization (experimental, CPU only)",
    )
    parser.add_argument(
        "--text-key", default="text", help="JSON key containing text (default: text)"
    )
    parser.add_argument(
        "--id-key", default="id", help="JSON key containing ID (default: id)"
    )

    args = parser.parse_args()

    # Validate input file
    if not Path(args.input_file).exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    # Generate embeddings
    generator = OptimizedEmbeddingGenerator(
        model_name=args.model,
        batch_size=args.batch_size,
        device="cpu",  # Recommended for your system
        quantize=args.quantize,
    )

    try:
        generator.embed_from_file(
            args.input_file,
            args.output_file,
            text_key=args.text_key,
            id_key=args.id_key,
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    main()
