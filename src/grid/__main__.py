from __future__ import annotations

# Suppress logging and warnings BEFORE any other imports
import logging
import os
import warnings

# Force quiet mode
os.environ["GRID_QUIET"] = "1"
os.environ["USE_DATABRICKS"] = "false"
os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Aggressively suppress logging before any heavy imports occur
logging.basicConfig(level=logging.CRITICAL, force=True)
logging.getLogger().setLevel(logging.CRITICAL)
logging.disable(logging.WARNING)

_noisy_loggers = [
    "application",
    "application.mothership",
    "application.mothership.config",
    "application.mothership.main",
    "application.mothership.security",
    "application.mothership.security.api_sentinels",
    "chromadb",
    "httpx",
    "sentence_transformers",
    "transformers",
    "huggingface_hub",
    "urllib3",
    "asyncio",
    "uvicorn",
    "fastapi",
]

for name in _noisy_loggers:
    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.handlers = []

# Suppress warnings globally
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import argparse
import ast
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, cast


def run_command(args: argparse.Namespace) -> int:
    """Handle 'grid run' subcommand for launching components."""
    component = args.component

    if component == "rag":
        # Launch interactive RAG chat
        try:
            import importlib

            chat_module = importlib.import_module("tools.rag.chat")
            ChatConfig = chat_module.ChatConfig
            interactive_loop = chat_module.interactive_loop
        except ImportError as e:
            raise SystemExit(f"Unable to import RAG chat module: {e}") from e

        config = ChatConfig(
            model=args.model,
            ollama_base_url=getattr(args, "ollama_url", "http://localhost:11434"),
            top_k=getattr(args, "top_k", 8),
            temperature=getattr(args, "temperature", 0.7),
            show_sources=not getattr(args, "no_sources", False),
            show_context=getattr(args, "show_context", False),
        )

        asyncio.run(interactive_loop(config))
        return 0

    elif component == "serve":
        return serve_command(args)

    else:
        print(f"Unknown component: {component}")
        print("Available: rag, serve")
        return 1


def chat_command(args: argparse.Namespace) -> int:
    """Handle interactive RAG chat command."""
    try:
        import importlib

        chat_module = importlib.import_module("tools.rag.chat")
        ChatConfig = chat_module.ChatConfig
    except ImportError as e:
        raise SystemExit(f"Unable to import RAG chat module: {e}") from e

    config = ChatConfig(
        model=args.model,
        ollama_base_url=args.ollama_url,
        top_k=args.top_k,
        temperature=args.temperature,
        show_sources=not args.no_sources,
        show_context=args.show_context,
    )

    # Single query mode
    if args.query:
        try:
            import importlib

            chat_module = importlib.import_module("tools.rag.chat")
            RAGChatSession = chat_module.RAGChatSession
        except ImportError as e:
            raise SystemExit(f"Unable to import RAG chat module: {e}") from e

        async def single_query():
            session = RAGChatSession(config)
            await session.initialize()
            await session.chat(args.query)
            return 0

        return asyncio.run(single_query())

    # Interactive mode
    try:
        import importlib

        chat_module = importlib.import_module("tools.rag.chat")
        interactive_loop = chat_module.interactive_loop
    except ImportError as e:
        raise SystemExit(f"Unable to import RAG chat module: {e}") from e

    asyncio.run(interactive_loop(config))
    return 0


def _read_text(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.text is None:
        raise SystemExit("TEXT is required unless --file is provided")
    return str(args.text)


def _format_output(payload: dict[str, Any], output: str) -> str:
    if output == "json":
        return json.dumps(payload, indent=2, ensure_ascii=False)

    if output == "yaml":
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise SystemExit(f"YAML output requested but PyYAML is not installed: {e}") from e
        return cast(str, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))

    if output == "table":
        lines = ["GRID Analyze Result", ""]
        lines.append(f"Text length: {len(payload.get('text', ''))}")
        lines.append(f"Entities: {len(payload.get('entities', []))}")
        lines.append(f"Relationships: {len(payload.get('relationships', []))}")
        if payload.get("note"):
            lines.append("")
            lines.append(str(payload["note"]))
        return "\n".join(lines)

    raise SystemExit(f"Unknown output format: {output}")


def analyze_command(args: argparse.Namespace) -> int:
    start = time.perf_counter()

    text = _read_text(args)

    init_end = time.perf_counter()

    payload: dict[str, Any] = {
        "text": text,
        "entities": [],
        "relationships": [],
        "confidence_threshold": args.confidence,
        "max_entities": args.max_entities,
        "use_rag": bool(args.use_rag),
    }

    if args.use_rag:
        payload["note"] = (
            "RAG is not available from this CLI in the current workspace snapshot. "
            "Use tools/rag/cli.py for RAG operations."
        )

    ner_end = time.perf_counter()
    rel_end = ner_end

    if args.timings:
        timings = {
            "init_ms": (init_end - start) * 1000,
            "ner_ms": (ner_end - init_end) * 1000,
            "relationships_ms": (rel_end - ner_end) * 1000,
            "total_ms": (rel_end - start) * 1000,
        }
        print(json.dumps(timings, indent=2), file=sys.stderr)

    sys.stdout.write(_format_output(payload, args.output))
    sys.stdout.write("\n")
    return 0


def serve_command(args: argparse.Namespace) -> int:
    try:
        import importlib

        server_module = importlib.import_module("application.mothership.main")
        server_main = server_module.main
    except Exception as e:
        raise SystemExit(f"Unable to import backend server entrypoint: {e}") from e

    server_main()
    return 0


def _read_json_payload(value: str | None, file: str | None) -> dict[str, Any]:
    if file:
        return cast(dict[str, Any], json.loads(Path(file).read_text(encoding="utf-8")))
    if value:
        raw = value
        value = value.strip()
        if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
            value = value[1:-1]
        try:
            return cast(dict[str, Any], json.loads(value))
        except json.JSONDecodeError:
            pass

        try:
            parsed = ast.literal_eval(value)
            if not isinstance(parsed, dict):
                raise SystemExit("Payload must decode to a JSON object/dict")
            return parsed
        except Exception:
            pass

        # PowerShell / JS-style object literal fallback: {key:1, other_key:"x"}
        # Supports identifier keys. Also attempts to quote bareword string values.
        if value.startswith("{") and value.endswith("}") and ":" in value:
            repaired = re.sub(r"([,{]\s*)([A-Za-z_][A-Za-z0-9_\-]*)\s*:", r'\1"\2":', value)
            # Quote single-quoted string values: {k:'v'} -> {"k":"v"}
            repaired = re.sub(r":\s*'([^']*)'\s*([,}])", r':"\1"\2', repaired)
            repaired = re.sub(
                r":\s*([A-Za-z_][A-Za-z0-9_\-]*)\s*([,}])",
                lambda m: (
                    f":{m.group(1)}{m.group(2)}"
                    if m.group(1) in {"true", "false", "null"}
                    else f':"{m.group(1)}"{m.group(2)}'
                ),
                repaired,
            )
            try:
                return cast(dict[str, Any], json.loads(repaired))
            except Exception:
                pass

        raise SystemExit(
            "Unable to parse payload. Provide valid JSON (use double quotes) "
            "or a Python literal dict/list string. Received: "
            f"{raw.strip()[:200]}"
        )
    return {}


def process_command(args: argparse.Namespace) -> int:
    try:
        from grid.application import IntelligenceApplication
    except Exception as e:
        raise SystemExit(f"Unable to import GRID application: {e}") from e

    data = _read_json_payload(args.data_json, args.data_file)
    context = _read_json_payload(args.context_json, args.context_file)

    app = IntelligenceApplication()

    result = asyncio.run(app.process_input(data, context, include_evidence=bool(args.evidence)))

    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


def skills_list_command(args: argparse.Namespace) -> int:
    from grid.skills.registry import default_registry

    payload = {
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
            }
            for s in default_registry.list()
        ]
    }

    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


def skills_run_command(args: argparse.Namespace) -> int:
    from grid.skills.registry import default_registry

    skill = default_registry.get(args.skill_id)
    if skill is None:
        raise SystemExit(f"Unknown skill: {args.skill_id}")

    skill_args: dict[str, Any] = {}
    if args.args_json or args.args_file:
        skill_args.update(_read_json_payload(args.args_json, args.args_file))

    # Convenience flags (don’t require JSON for common use-cases)
    if getattr(args, "transcript_file", None):
        skill_args.setdefault("transcript_file", args.transcript_file)
    if getattr(args, "use_rag", False):
        skill_args.setdefault("use_rag", True)
    if getattr(args, "top_n", None) is not None:
        skill_args.setdefault("top_n", args.top_n)

    result = skill.run(skill_args)

    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


def storytime_command(args: argparse.Namespace) -> int:
    stories = {
        "synthwave origins": """
# GRID: Synthwave Origins

In the neon-soaked corridors of the digital frontier, GRID was forged—not just as code, but as a resonance of the 1980s' digital dreams.

## The Vision
Inspired by Kevin Flynn's journey into the Grid (Walt Disney Pictures' TRON), GRID aims to bridge the gap between human intuition and computational logic. It is a world where programs are living entities, data flows like light cycles, and every interaction leaves a trail of geometric energy.

## The Aesthetic
- **Neon on Dark**: High-contrast interfaces designed for focus and rhythm.
- **Rhythmic Processing**: Concepts like "Flow", "Rhythm", and "Resonance" are baked into the core intelligence.
- **Circuit Architecture**: Data moves through constraint-based pathways, just like the glowing traces of a mainframe.

## The Evolution
From a simple NER tool to a comprehensive "Geometric Resonance Intelligence Driver," GRID has evolved to help you navigate the complexity of modern systems with the grace of a user in a digital realm.

*“The Grid. A digital frontier. I tried to picture clusters of information as they moved through the computer...”*
""",
    }

    topic = (args.topic or "").lower().strip()
    story = stories.get(topic)

    if not story:
        print(f"Lore not found for topic: '{topic}'", file=sys.stderr)
        print("Available stories: " + ", ".join(f"'{s}'" for s in stories.keys()), file=sys.stderr)
        return 1

    sys.stdout.write(story.strip())
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="grid")
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser("analyze", help="Analyze text (fallback implementation)")
    analyze.add_argument("text", nargs="?", help="Text to analyze")
    analyze.add_argument("--file", help="Read text from file")
    analyze.add_argument("--output", choices=["json", "table", "yaml"], default="table")
    analyze.add_argument("--use-rag", action="store_true", default=False)
    analyze.add_argument("--openai-key")
    analyze.add_argument("--confidence", type=float, default=0.7)
    analyze.add_argument("--max-entities", type=int, default=0)
    analyze.add_argument("--timings", action="store_true", default=False)
    analyze.add_argument("--debug", action="store_true", default=False)
    analyze.set_defaults(func=analyze_command)

    serve = subparsers.add_parser("serve", help="Run the local Mothership backend server")
    serve.set_defaults(func=serve_command)

    process = subparsers.add_parser("process", help="Process a payload through the GRID intelligence pipeline")
    process.add_argument("--data-json", help="JSON string for the input data")
    process.add_argument("--data-file", help="Path to JSON file for the input data")
    process.add_argument("--context-json", help="JSON string for the context parameters")
    process.add_argument("--context-file", help="Path to JSON file for the context parameters")
    process.add_argument("--evidence", action="store_true", default=False)
    process.set_defaults(func=process_command)

    skills = subparsers.add_parser("skills", help="List and run GRID skills")
    skills_sub = skills.add_subparsers(dest="skills_command")

    skills_list = skills_sub.add_parser("list", help="List available skills")
    skills_list.set_defaults(func=skills_list_command)

    skills_run = skills_sub.add_parser("run", help="Run a skill")
    skills_run.add_argument("skill_id", help="Skill ID to run")
    skills_run.add_argument("--args-json", help="JSON string of skill args")
    skills_run.add_argument("--args-file", help="Path to JSON file of skill args")
    skills_run.add_argument("--transcript-file", help="Convenience: transcript file path")
    skills_run.add_argument("--use-rag", action="store_true", default=False)
    skills_run.add_argument("--top-n", type=int, default=None)
    skills_run.set_defaults(func=skills_run_command)

    storytime = subparsers.add_parser("storytime", help="Explore the lore and origins of GRID")
    storytime.add_argument("topic", help="The topic to explore (e.g., 'synthwave origins')")
    storytime.set_defaults(func=storytime_command)

    # Interactive RAG chat command
    chat = subparsers.add_parser(
        "chat",
        help="Interactive RAG chat - talk to your codebase",
        description="Start an interactive chat session with your codebase using RAG-augmented LLM",
    )
    chat.add_argument("--model", "-m", default="ministral-3:3b", help="Ollama model to use (default: ministral-3:3b)")
    chat.add_argument("--top-k", "-k", type=int, default=8, help="Number of context chunks to retrieve")
    chat.add_argument("--temperature", "-t", type=float, default=0.7, help="LLM temperature")
    chat.add_argument("--no-sources", action="store_true", help="Don't show retrieved sources")
    chat.add_argument("--show-context", action="store_true", help="Show full retrieved context (debug)")
    chat.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL")
    chat.add_argument("--query", "-q", help="Single query mode (non-interactive)")
    chat.set_defaults(func=chat_command)

    # Run command - unified way to launch components with model selection
    run = subparsers.add_parser(
        "run",
        help="Run GRID components (e.g., grid run rag --model ministral-3:3b)",
        description="Launch GRID components with optional model configuration",
    )
    run_sub = run.add_subparsers(dest="component", help="Component to run")

    # grid run rag [--model X]
    run_rag = run_sub.add_parser(
        "rag",
        help="Interactive RAG chat with your codebase",
        description="Start an interactive chat session with RAG-augmented LLM",
    )
    run_rag.add_argument(
        "--model",
        "-m",
        default="ministral-3:3b",
        help="Ollama model (e.g., ministral-3:3b, qwen2.5-coder:latest)",
    )
    run_rag.add_argument("--top-k", "-k", type=int, default=8, help="Context chunks to retrieve")
    run_rag.add_argument("--temperature", "-t", type=float, default=0.7, help="LLM temperature")
    run_rag.add_argument("--no-sources", action="store_true", help="Hide source references")
    run_rag.add_argument("--show-context", action="store_true", help="Show full context (debug)")
    run_rag.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama URL")
    run_rag.set_defaults(func=run_command)

    # grid run serve
    run_serve = run_sub.add_parser("serve", help="Run the Mothership API server")
    run_serve.set_defaults(func=run_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        parser.print_help()
        return 1

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1

    if getattr(args, "debug", False):
        debug_payload = {
            "command": args.command,
            "python": sys.version,
            "executable": sys.executable,
            "cwd": str(Path.cwd()),
        }
        print(json.dumps(debug_payload, indent=2), file=sys.stderr)

    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
