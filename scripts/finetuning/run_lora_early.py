"""
Early-stage LoRA fine-tuning: minimal run to validate the practical stack.

Uses a small model (TinyLlama 1.1B), PEFT LoRA, 1 epoch, capped steps.
Saves adapter to out/early_lora. Run after: uv sync --group finetuning.

Usage (from repo root):
  uv run python scripts/finetuning/run_lora_early.py
  uv run python scripts/finetuning/run_lora_early.py --max_steps 20 --output_dir out/quick
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

# Optional: reduce logging noise from transformers/torch
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Early-stage LoRA run (fast iteration).")
    p.add_argument(
        "--model",
        type=str,
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        help="Hugging Face model id (small model for CPU/single GPU).",
    )
    p.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Adapter output directory (default: scripts/finetuning/out/early_lora).",
    )
    p.add_argument(
        "--max_steps",
        type=int,
        default=50,
        help="Max training steps for early try-out (default 50).",
    )
    p.add_argument(
        "--lora_r",
        type=int,
        default=8,
        help="LoRA rank (default 8; increase for more capacity).",
    )
    p.add_argument(
        "--batch_size",
        type=int,
        default=2,
        help="Per-device batch size (default 2).",
    )
    return p.parse_args()


def _default_output_dir() -> Path:
    script_dir = Path(__file__).resolve().parent
    return script_dir / "out" / "early_lora"


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as e:
        raise SystemExit("Missing finetuning deps. Run: uv sync --group finetuning") from e

    model_id = args.model
    print(f"Loading base model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    if model.device.type == "cpu":
        print("Running on CPU (no CUDA). Use a small model and low max_steps for quick try-out.")

    # LoRA config: only train adapters
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Minimal synthetic data: few examples so the run finishes quickly
    num_examples = min(32, args.max_steps * args.batch_size)
    texts = ["Instruction: Say hello.\nResponse: Hello! How can I help?" for _ in range(num_examples)]
    dataset = Dataset.from_dict({"text": texts})

    def tokenize(examples: dict) -> dict:
        out = tokenizer(
            examples["text"],
            truncation=True,
            max_length=128,
            padding="max_length",
            return_tensors=None,
        )
        # Causal LM: labels = input_ids, mask padding with -100
        out["labels"] = [[tid if tid != tokenizer.pad_token_id else -100 for tid in ids] for ids in out["input_ids"]]
        return out

    tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)
    tokenized.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        logging_steps=10,
        save_strategy="steps",
        save_steps=args.max_steps,
        save_total_limit=1,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=data_collator,
    )

    print(f"Training for max_steps={args.max_steps}, output_dir={output_dir}")
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Adapter and tokenizer saved to {output_dir}")


if __name__ == "__main__":
    main()
