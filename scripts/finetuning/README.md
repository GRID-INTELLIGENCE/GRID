# Fine-tuning practical stack (option 3)

Fast iteration for **early-stage** LoRA fine-tuning: small adapter training, 1–2 epochs, minimal data, so you can try out next steps in training without full runs.

## Stack

- **PEFT (LoRA)**: train only adapter weights (~&lt;1% of params); less memory, faster steps.
- **Transformers + Accelerate**: load base model, training loop, device placement.
- **Datasets**: load small HF datasets or synthetic data for quick experiments.

Optional later: **QLoRA** (add `bitsandbytes`) for 4-bit base + LoRA on GPU; **Unsloth** or **Axolotl** for config-driven runs.

## Install

From repo root:

```bash
uv sync --group finetuning
```

This adds: `torch`, `transformers`, `peft`, `datasets`, `accelerate`. No CUDA required for the minimal script (runs on CPU with a tiny model).

## Run early-stage LoRA (minimal)

```bash
# From repo root, with PYTHONPATH so scripts can import
uv run python scripts/finetuning/run_lora_early.py
```

Defaults: **TinyLlama-1.1B-Chat** (small, CPU-friendly), LoRA rank 8, 1 epoch, 50 steps max, synthetic data. Saves adapter to `scripts/finetuning/out/early_lora`.

Options (edit `run_lora_early.py` or add argparse):

- `--model`: Hugging Face model id (default TinyLlama).
- `--output_dir`: where to save the adapter (default `scripts/finetuning/out/early_lora`).
- `--max_steps`: cap steps for fast try-out (default 50).
- `--lora_r`: LoRA rank (default 8; increase for more capacity, slower).

## Next steps after early run

1. **Larger model / QLoRA**: Use a 7B model with 4-bit quantization + LoRA (add `bitsandbytes`, set `load_in_4bit=True` in script).
2. **Real data**: Replace synthetic data with `datasets.load_dataset(...)` and your SFT/instruction data.
3. **Export for Ollama**: Merge adapter into base and export to GGUF, or use Ollama’s import path if supported for your model.
4. **Unsloth / Axolotl**: For 2x speed and config-driven runs, add Unsloth or Axolotl and point at this repo’s data/output layout.

## References

- [MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md](../../docs/MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md) — context for local-first and model usage.
- PEFT: https://huggingface.co/docs/peft  
- LoRA: low-rank adaptation, train only adapters.
