#!/usr/bin/env python3
"""
EUFLE REPL (no backend)
Lightweight discussion loop that collects questions and prints responses.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
import code
import math


@dataclass
class DialogueTurn:
    question: str
    response: str


@dataclass
class EufleRepl:
    history: List[DialogueTurn] = field(default_factory=list)
    run_template: str = "run(\"{question}\") -> {response}"
    stop_template: str = "stop(\"{question}\") -> {response}"
    volume: float = 1.0
    eufle_readme_path: Path = Path(r"E:\EUFLE\README.md")

    def respond(self, question: str) -> str:
        if not question:
            return ""
        lowered = question.lower()
        if "eufle" in lowered:
            return self._eufle_summary()
        return f"[EUFLE Studio pending] Received: {question}"

    def _eufle_summary(self) -> str:
        if not self.eufle_readme_path.exists():
            return "EUFLE README not found at E:\\EUFLE\\README.md"
        lines = self.eufle_readme_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        summary_lines = [line.strip() for line in lines[:12] if line.strip()]
        summary = " ".join(summary_lines)
        return summary

    def volume_to_db(self, ratio: float) -> float:
        safe_ratio = max(1e-6, min(1.0, ratio))
        return 20.0 * math.log10(safe_ratio)

    def db_to_ratio(self, db: float) -> float:
        return 10 ** (db / 20.0)

    def render(self, template: str, question: str) -> str:
        response = self.respond(question)
        volume_db = self.volume_to_db(self.volume)
        ratio = self.db_to_ratio(volume_db)
        if ratio < 1.0 and response:
            max_len = max(1, int(len(response) * ratio))
            response = response[:max_len]
        return template.format(question=question, response=response)

    def set_volume(self, level: float) -> None:
        """Set verbosity level (0-1 ratio)."""
        self.volume = max(0.0, min(1.0, level))
        print(f"Volume set to {self.volume * 100:.0f}%")

    def run(self, question: str) -> str:
        return self.render(self.run_template, question)

    def stop(self, question: str = ".") -> Optional[str]:
        if question.strip() == ".":
            code.interact(local={"repl": self})
            return "Python interpreter exited."
        if question.strip().lower() in {"repl", "start"}:
            self.repl()
            return None
        return self.render(self.stop_template, question)

    def repl(self) -> None:
        print("EUFLE REPL (type 'exit' to quit)")
        while True:
            question = input("Q> ").strip()
            if not question:
                continue
            if question.lower() in {"exit", "quit"}:
                break
            if question.lower().startswith("volume "):
                _, level = question.split(" ", 1)
                self.set_volume(float(level))
                continue
            response = self.respond(question)
            self.history.append(DialogueTurn(question=question, response=response))
            print(f"A> {response}")


if __name__ == "__main__":
    EufleRepl().repl()
