from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from .base import SimpleSkill

_PRONOUNS = re.compile(
    r"\b(i|me|my|mine|we|us|our|ours|you|your|yours|he|him|his|she|her|hers|they|them|their|theirs|it|its|this|that|these|those)\b",
    re.IGNORECASE,
)


def _normalize_text(text: str, pronoun_minimize: bool) -> str:
    cleaned = text.strip()
    if pronoun_minimize:
        cleaned = _PRONOUNS.sub("", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _extract_json_object(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```\s*$", "", stripped)
        stripped = stripped.strip()
    try:
        return json.loads(stripped)
    except Exception:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        return json.loads(candidate)
    return json.loads(stripped)


def _schema_spec(name: str) -> dict[str, Any]:
    key = (name or "").strip().lower()

    if key in {"default", "grid", "facts"}:
        return {
            "name": "default",
            "sections": ["facts", "assumptions", "goals", "constraints", "next_actions"],
            "template": {
                "facts": [],
                "assumptions": [],
                "goals": [],
                "constraints": [],
                "next_actions": [],
            },
        }

    if key in {"sensory", "senses"}:
        return {
            "name": "sensory",
            "sections": [
                "sight",
                "sound",
                "taste",
                "smell",
                "touch",
                "sixth_sense",
                "unified_trigger",
            ],
            "template": {
                "sight": {"element": "", "essence": "", "modes": []},
                "sound": {"element": "", "essence": "", "modes": []},
                "taste": {"element": "", "essence": "", "modes": []},
                "smell": {"element": "", "essence": "", "modes": []},
                "touch": {"element": "", "essence": "", "modes": []},
                "sixth_sense": {"element": "", "essence": "", "modes": []},
                "unified_trigger": {"function": "", "purpose": ""},
            },
        }

    if key in {"resonance"}:
        return {
            "name": "resonance",
            "sections": [
                "principles",
                "activate_mystique",
                "implementation_notes",
            ],
            "template": {
                "principles": [],
                "activate_mystique": {"purpose": "", "how_it_works": [], "why_it_works": [], "examples": []},
                "implementation_notes": [],
            },
        }

    if key in {"ai_safety", "safety", "ai safety"}:
        return {
            "name": "ai_safety",
            "sections": [
                "value_proposition",
                "architecture",
                "safety_security",
                "privacy",
                "human_rights_ethics",
                "accountability",
                "monitoring_maintenance",
            ],
            "template": {
                "value_proposition": [],
                "architecture": [],
                "safety_security": [],
                "privacy": [],
                "human_rights_ethics": [],
                "accountability": [],
                "monitoring_maintenance": [],
            },
        }

    if key in {"context_engineering", "context engineering", "tcos"}:
        return {
            "name": "context_engineering",
            "sections": [
                "mandate",
                "vector_memory",
                "retrieval_logic",
                "contradiction_resolution",
                "agentic_planning_alignment",
                "cost_controls",
                "next_actions",
            ],
            "template": {
                "mandate": [],
                "vector_memory": [],
                "retrieval_logic": [],
                "contradiction_resolution": [],
                "agentic_planning_alignment": [],
                "cost_controls": [],
                "next_actions": [],
            },
        }

    if key in {"knowledgebase", "shield_sword", "shield-sword"}:
        return {
            "name": "knowledgebase",
            "sections": [
                "shield_safe_core",
                "sword_consequences",
                "scopes_timeframes",
                "consistency_overwhelm_prevention",
                "feedback_loops",
            ],
            "template": {
                "shield_safe_core": [],
                "sword_consequences": [],
                "scopes_timeframes": [],
                "consistency_overwhelm_prevention": [],
                "feedback_loops": [],
            },
        }

    if key in {"mentorpsyche", "mentor_psyche"}:
        return {
            "name": "mentorpsyche",
            "sections": [
                "foundational_principles",
                "core_objectives",
                "tools_methods",
                "stages",
                "roles",
                "community_long_term",
                "implementation_suggestions",
            ],
            "template": {
                "foundational_principles": [],
                "core_objectives": [],
                "tools_methods": [],
                "stages": [],
                "roles": [],
                "community_long_term": [],
                "implementation_suggestions": [],
            },
        }

    return {
        "name": "default",
        "sections": ["facts", "assumptions", "goals", "constraints", "next_actions"],
        "template": {
            "facts": [],
            "assumptions": [],
            "goals": [],
            "constraints": [],
            "next_actions": [],
        },
    }


def _split_sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [s.strip() for s in raw if s and s.strip()]


def _bucket_by_keywords(sentences: list[str], buckets: dict[str, list[str]]) -> tuple[dict[str, list[str]], list[str]]:
    out: dict[str, list[str]] = {k: [] for k in buckets.keys()}
    unmapped: list[str] = []

    for s in sentences:
        low = s.lower()
        placed = False
        for key, kws in buckets.items():
            if any(kw in low for kw in kws):
                out[key].append(s)
                placed = True
                break
        if not placed:
            unmapped.append(s)

    return out, unmapped


def _parse_sensory(text: str) -> tuple[dict[str, Any], list[str]]:
    # Designed to parse the exact structure in sensory.md.
    prepared = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize common inline formats into something line-oriented.
    # Example: "Sight (...) Element: Light Essence: Clarity Modes: - Focusing - Refracting"
    headers = ["Sight", "Sound", "Taste", "Smell", "Touch", "Sixth Sense", "Unified Trigger"]
    for hdr in headers:
        prepared = re.sub(rf"(?<!\n)\b{re.escape(hdr)}\b", f"\n{hdr}", prepared, flags=re.IGNORECASE)

    for marker in ["Element:", "Essence:", "Modes:", "Function:", "Purpose:"]:
        prepared = re.sub(rf"(?i)\s*{re.escape(marker)}", f"\n{marker}", prepared)

    # Turn inline bullets into one-per-line bullets.
    prepared = re.sub(r"\s+-\s+", "\n- ", prepared)

    lines = [ln.rstrip() for ln in prepared.splitlines() if ln.strip()]
    unmapped: list[str] = []

    def _init_sense() -> dict[str, Any]:
        return {"element": "", "essence": "", "modes": []}

    out: dict[str, Any] = {
        "sight": _init_sense(),
        "sound": _init_sense(),
        "taste": _init_sense(),
        "smell": _init_sense(),
        "touch": _init_sense(),
        "sixth_sense": _init_sense(),
        "unified_trigger": {"function": "", "purpose": ""},
    }

    current: str | None = None
    for ln in lines:
        head = ln.split("(")[0].strip().lower()
        if head in {"sight", "sound", "taste", "smell", "touch", "sixth sense", "unified trigger"}:
            if head == "sixth sense":
                current = "sixth_sense"
            elif head == "unified trigger":
                current = "unified_trigger"
            else:
                current = head
            continue

        if current is None:
            unmapped.append(ln)
            continue

        if current == "unified_trigger":
            if ln.lower().startswith("function:"):
                out["unified_trigger"]["function"] = ln.split(":", 1)[1].strip()
            elif ln.lower().startswith("purpose:"):
                out["unified_trigger"]["purpose"] = ln.split(":", 1)[1].strip()
            else:
                unmapped.append(ln)
            continue

        if ln.lower().startswith("element:"):
            out[current]["element"] = ln.split(":", 1)[1].strip()
        elif ln.lower().startswith("essence:"):
            out[current]["essence"] = ln.split(":", 1)[1].strip()
        elif ln.lower().startswith("modes:"):
            # just a marker
            continue
        elif ln.lstrip().startswith("-"):
            mode = ln.lstrip()[1:].strip()
            if mode:
                out[current]["modes"].append(mode)
        else:
            unmapped.append(ln)

    return out, unmapped


def _heuristic_custom_schema(schema_name: str, text: str) -> tuple[dict[str, Any], list[str]]:
    sentences = _split_sentences(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    if schema_name == "sensory":
        return _parse_sensory(text)

    if schema_name == "knowledgebase":
        buckets, unmapped = _bucket_by_keywords(
            sentences,
            {
                "shield_safe_core": ["shield", "safe core", "gold-standard", "vetted", "protected"],
                "sword_consequences": ["sword", "consequence", "strike", "role-based", "access"],
                "scopes_timeframes": ["scope", "timeframe", "phased", "milestone", "checkpoint", "ring"],
                "consistency_overwhelm_prevention": ["overwhelm", "gradual", "incremental", "consistency", "prevent"],
                "feedback_loops": ["feedback", "check-in", "monitor", "alert", "audit"],
            },
        )
        return buckets, unmapped

    if schema_name == "resonance":
        unmapped = []

        # Extract numbered principles (handles emoji numbers, plain numbered lists, and inline 1) 2) 3) sequences)
        principles: list[str] = []
        in_principles = False
        for ln in lines:
            low = ln.lower()
            if "six core" in low and "princip" in low:
                in_principles = True
                continue
            if in_principles:
                if "mystique" in low and "activation" in low:
                    in_principles = False
                elif re.match(r"^(\d+|[0-9]️⃣|[0-9]⃣)", ln) or ln.startswith("-"):
                    principles.append(ln.lstrip("- ").strip())
                elif low.startswith("---"):
                    continue

        # Inline numbered principles: "1) ... 2) ... 3) ..."
        inline_parts = re.split(r"\s+(?=\d+\))", text.strip())
        if len(inline_parts) > 1:
            for part in inline_parts:
                m = re.match(r"^(\d+)\)\s*(.+)$", part.strip())
                if m:
                    content = m.group(2).strip()
                    # If Mystique Activation appears inline after the last principle, keep it out of principles.
                    cut = re.split(r"(?i)\bmystique activation\b", content, maxsplit=1)
                    content = cut[0].strip().rstrip(".:;-")
                    if content:
                        principles.append(content)

        activate: dict[str, Any] = {"purpose": "", "how_it_works": [], "why_it_works": [], "examples": []}
        in_mystique = False
        current_block: str | None = None
        for ln in lines:
            low = ln.lower()
            if "mystique" in low and "activation" in low:
                in_mystique = True
                current_block = None
                continue
            if not in_mystique:
                continue
            if low.startswith("---"):
                continue
            if low.startswith("purpose"):
                current_block = "purpose"
                continue
            if "how it works" in low:
                current_block = "how_it_works"
                continue
            if "why it works" in low:
                current_block = "why_it_works"
                continue
            if low.startswith("examples"):
                current_block = "examples"
                continue
            if low.startswith("ready for implementation"):
                in_mystique = False
                current_block = None
                continue

            # Content lines
            content = ln.lstrip("- ").strip()
            if not content:
                continue
            if current_block == "purpose" and not activate["purpose"]:
                activate["purpose"] = content
            elif current_block in {"how_it_works", "why_it_works", "examples"}:
                activate[current_block].append(content)
            elif "what would" in low:
                activate["examples"].append(content)

        # Inline Mystique Activation blocks (single-line): parse label spans.
        if "mystique activation" in text.lower():
            # Normalize spacing so regex splitting is easier
            flat = re.sub(r"\s+", " ", text).strip()
            # Grab the substring after Mystique Activation (if present)
            idx = flat.lower().find("mystique activation")
            if idx != -1:
                flat = flat[idx:]

            def _grab(label: str) -> str:
                m = re.search(
                    rf"(?i){label}\s*:\s*(.*?)\s*(?=(purpose|how it works|why it works|examples)\s*:|$)", flat
                )
                return m.group(1).strip() if m else ""

            purpose = _grab("purpose")
            how = _grab("how it works")
            why = _grab("why it works")
            examples = _grab("examples")

            if purpose and not activate["purpose"]:
                activate["purpose"] = purpose
            if how:
                activate["how_it_works"].extend([x.strip() for x in re.split(r"[;\n]", how) if x.strip()])
            if why:
                activate["why_it_works"].extend([x.strip() for x in re.split(r"[;\n]", why) if x.strip()])
            if examples:
                activate["examples"].extend([x.strip() for x in re.split(r"[;\n]", examples) if x.strip()])

        # Keep a small implementation hint section
        implementation_notes = []
        for ln in lines:
            low = ln.lower()
            if "ready for implementation" in low or "testing" in low:
                implementation_notes.append(ln)

        if not principles:
            # fallback keyword bucketing
            buckets, extra_unmapped = _bucket_by_keywords(
                sentences,
                {
                    "principles": ["principle", "core", "breaking", "balancing", "iterative", "recharge", "chaos"],
                    "implementation_notes": ["implementation", "ready", "application", "test"],
                },
            )
            principles = buckets.get("principles", [])
            if not implementation_notes:
                implementation_notes = buckets.get("implementation_notes", [])
            unmapped.extend(extra_unmapped)

        out = {"principles": principles, "activate_mystique": activate, "implementation_notes": implementation_notes}
        return out, unmapped

    if schema_name == "context_engineering":
        buckets, unmapped = _bucket_by_keywords(
            sentences,
            {
                "mandate": ["mandate", "thesis", "architectural", "context engineering", "tcos"],
                "vector_memory": ["vector", "embedding", "vector-based", "database", "index"],
                "retrieval_logic": ["retrieval", "recall", "semantic", "primary recall", "contextual recall"],
                "contradiction_resolution": ["contradiction", "conflict", "consistency", "resolution"],
                "agentic_planning_alignment": [
                    "agent",
                    "fast",
                    "fastee",
                    "fastex",
                    "stepbloom",
                    "checkpoint",
                    "planning",
                ],
                "cost_controls": ["cost", "latency", "thinking_level", "budget", "optimiz"],
                "next_actions": ["recommendation", "strategic action", "immediate", "next", "implement"],
            },
        )

        # Inline label parsing (single paragraph / CES-style summaries)
        flat = re.sub(r"\s+", " ", text).strip()

        def _grab(label: str) -> str:
            # Use non-capturing groups to avoid group-index confusion when `label` contains alternations.
            m = re.search(
                rf"(?i)\b(?:{label})\b\s*:\s*(?P<content>.*?)\s*(?=(?:context engineering service|ces|tcos|vector memory|retrieval logic|contradiction resolution|contradiction|cost controls?|cost management|next actions?|next|recommendation)\b\s*:|$)",
                flat,
            )
            return (m.group("content") or "").strip() if m else ""

        # Common inline labels
        mandate_txt = _grab("context engineering service|ces|tcos")
        if mandate_txt:
            buckets["mandate"].append(mandate_txt)

        vec_txt = _grab("vector memory")
        if vec_txt:
            buckets["vector_memory"].append(vec_txt)

        retrieval_txt = _grab("retrieval logic")
        if retrieval_txt:
            buckets["retrieval_logic"].append(retrieval_txt)

        contra_txt = _grab("contradiction resolution")
        if contra_txt:
            buckets["contradiction_resolution"].append(contra_txt)

        cost_txt = _grab("cost controls?|cost management")
        if cost_txt:
            buckets["cost_controls"].append(cost_txt)

        next_txt = _grab("next actions?|next|recommendation")
        if next_txt:
            buckets["next_actions"].append(next_txt)

        # Also extract explicit recall sub-items if present in-line.
        recall_items = []
        for token in re.split(r"[,;]", retrieval_txt or ""):
            t = token.strip()
            if not t:
                continue
            if re.search(r"(?i)primary recall|contextual recall|contradiction flagging", t):
                recall_items.append(t)
        if recall_items:
            merged = buckets.get("retrieval_logic", [])
            merged.extend([x for x in recall_items if x not in merged])
            buckets["retrieval_logic"] = merged

        # Enhance retrieval_logic with explicit recall bullets if present in line form.
        recall_lines: list[str] = []
        in_retrieval = False
        for ln in lines:
            low = ln.lower()
            if "retrieval" in low and "logic" in low:
                in_retrieval = True
                continue
            if in_retrieval:
                if low.startswith("2.") or low.startswith("3.") or low.startswith("part"):
                    in_retrieval = False
                    continue
                if any(x in low for x in ["primary recall", "contextual recall", "contradiction flagging"]):
                    recall_lines.append(ln)
                if ln.startswith("-") and any(x in low for x in ["primary", "contextual", "contradiction"]):
                    recall_lines.append(ln.lstrip("- ").strip())

        if recall_lines:
            merged = buckets.get("retrieval_logic", [])
            merged.extend([x for x in recall_lines if x not in merged])
            buckets["retrieval_logic"] = merged

        # Normalize: strip label prefixes and prefer atomic values.
        def _strip_prefix(value: str, labels: list[str]) -> str:
            v = value.strip()
            for lab in labels:
                v = re.sub(rf"(?i)^\s*{lab}\s*:\s*", "", v).strip()
            return v

        buckets["mandate"] = [
            _strip_prefix(v, [r"context engineering service", r"ces", r"tcos", r"mandate"])
            for v in buckets.get("mandate", [])
        ]
        buckets["vector_memory"] = [_strip_prefix(v, [r"vector memory"]) for v in buckets.get("vector_memory", [])]
        buckets["contradiction_resolution"] = [
            _strip_prefix(v, [r"contradiction resolution", r"contradiction"])
            for v in buckets.get("contradiction_resolution", [])
        ]
        buckets["cost_controls"] = [
            _strip_prefix(v, [r"cost controls?", r"cost management"]) for v in buckets.get("cost_controls", [])
        ]

        # Normalize next_actions: strip label and split semicolon-separated items.
        next_clean: list[str] = []
        for v in buckets.get("next_actions", []):
            vv = _strip_prefix(v, [r"next actions?", r"next", r"recommendation"]).rstrip(".")
            for part in re.split(r"[;\n]", vv):
                p = part.strip().rstrip(".")
                if p:
                    next_clean.append(p)
        buckets["next_actions"] = next_clean

        # Normalize retrieval_logic: strip label; if it is just a list of recall items, prefer atomic items.
        recall_terms = ["primary recall", "contextual recall", "contradiction flagging"]
        recall_atoms: list[str] = []
        retrieval_other: list[str] = []
        for v in buckets.get("retrieval_logic", []):
            vv = _strip_prefix(v, [r"retrieval logic"]).strip().rstrip(".")
            if not vv:
                continue
            parts = [p.strip().rstrip(".") for p in re.split(r"[,;]", vv) if p.strip()]
            matched = []
            for p in parts:
                if any(rt in p.lower() for rt in recall_terms):
                    matched.append(p)
            if matched and len(matched) == len(parts):
                recall_atoms.extend(matched)
            else:
                retrieval_other.append(vv)
                recall_atoms.extend(matched)
        buckets["retrieval_logic"] = retrieval_other + recall_atoms

        # If "Next:" lines were captured under agentic_planning_alignment, drop them when next_actions exists.
        next_set = {v.strip().rstrip(".") for v in buckets.get("next_actions", []) if v.strip()}
        agentic_clean: list[str] = []
        for v in buckets.get("agentic_planning_alignment", []):
            vv = _strip_prefix(v, [r"next actions?", r"next", r"recommendation"]).strip().rstrip(".")
            if not vv:
                continue

            parts = [p.strip().rstrip(".") for p in re.split(r"[;\n]", vv) if p.strip()]
            keep_keywords = ["stepbloom", "if-then", "checkpoint", "fastee", "fastex", "fast"]
            kept_any = False
            for p in parts or [vv]:
                low = p.lower()
                if any(k in low for k in keep_keywords):
                    agentic_clean.append(p)
                    kept_any = True

            # If this agentic line is purely duplicated next_actions and contains no planning keywords, drop it.
            if not kept_any and parts and next_set and all(p in next_set for p in parts):
                continue
        buckets["agentic_planning_alignment"] = agentic_clean

        # De-duplicate within each bucket
        for k, v in buckets.items():
            if not isinstance(v, list):
                continue
            seen = set()
            deduped = []
            for item in v:
                key = item.strip()
                if not key or key in seen:
                    continue
                seen.add(key)
                deduped.append(item)
            buckets[k] = deduped

        return buckets, unmapped

    if schema_name == "ai_safety":
        buckets, unmapped = _bucket_by_keywords(
            sentences,
            {
                "value_proposition": ["value proposition", "offers", "designed"],
                "architecture": ["architecture", "core components", "modules"],
                "safety_security": ["safety", "security", "risk", "shield"],
                "privacy": ["privacy", "consent", "encryption", "data"],
                "human_rights_ethics": ["human rights", "ethical", "fairness", "bias"],
                "accountability": ["accountability", "reward", "override", "audit"],
                "monitoring_maintenance": ["monitor", "maintenance", "future", "feedback loop"],
            },
        )
        return buckets, unmapped

    if schema_name == "mentorpsyche":
        buckets, unmapped = _bucket_by_keywords(
            sentences,
            {
                "foundational_principles": ["foundational", "self-awareness", "shadow", "individuation"],
                "core_objectives": ["objective", "milestone", "growth", "recovery"],
                "tools_methods": ["tools", "methods", "dream", "journaling", "archetype"],
                "stages": ["awareness", "confrontation", "integration", "connection", "transformation"],
                "roles": ["therapist", "client", "evaluator", "facilitator", "participant"],
                "community_long_term": ["community", "peer", "mentorship", "long-term"],
                "implementation_suggestions": ["implementation", "suggestion", "practical"],
            },
        )
        return buckets, unmapped

    # fallback to default heuristic
    return _heuristic_default_schema(text), []


def _heuristic_default_schema(text: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    facts = []
    goals = []
    constraints = []
    next_actions = []
    assumptions = []

    for ln in lines:
        low = ln.lower()
        if low.startswith("goal") or "objective" in low:
            goals.append(ln)
        elif low.startswith("constraint") or "must" in low or "cannot" in low:
            constraints.append(ln)
        elif low.startswith("next") or low.startswith("action") or low.startswith("todo"):
            next_actions.append(ln)
        elif "assume" in low or low.startswith("assumption"):
            assumptions.append(ln)
        else:
            facts.append(ln)

    return {
        "facts": facts[:20],
        "assumptions": assumptions[:20],
        "goals": goals[:20],
        "constraints": constraints[:20],
        "next_actions": next_actions[:20],
    }


def _transform(args: Mapping[str, Any]) -> dict[str, Any]:
    text = args.get("text") or args.get("input")
    if text is None:
        return {
            "skill": "transform.schema_map",
            "status": "error",
            "error": "Missing required parameter: 'text'",
        }

    target_schema = str(args.get("target_schema") or args.get("targetSchema") or "default")
    output_format = str(args.get("output_format") or args.get("outputFormat") or "json").lower()
    pronoun_minimize = bool(args.get("pronoun_minimize") or args.get("pronounMinimize"))
    use_llm = bool(args.get("use_llm") or args.get("useLLM"))

    raw = str(text)
    normalized = _normalize_text(raw, pronoun_minimize=pronoun_minimize)
    spec = _schema_spec(target_schema)

    if use_llm:
        try:
            import importlib

            rag_config_module = importlib.import_module("tools.rag.config")
            rag_llm_module = importlib.import_module("tools.rag.llm.factory")
            RAGConfig = rag_config_module.RAGConfig
            get_llm_provider = rag_llm_module.get_llm_provider

            config = RAGConfig.from_env()
            config.ensure_local_only()
            llm = get_llm_provider(config=config)

            template = spec.get("template", {})
            prompt = (
                "Transform the input text into the requested schema.\n"
                "Rules:\n"
                "- Preserve meaning; do not invent facts.\n"
                "- Prefer concrete nouns; minimize pronouns.\n"
                "- If a field is unknown, keep the default empty value from the template.\n"
                "- Output MUST be valid JSON and MUST match the template keys.\n\n"
                f"TARGET_SCHEMA: {spec['name']}\n"
                f"JSON_TEMPLATE: {json.dumps(template, ensure_ascii=False)}\n\n"
                f"TEXT:\n{normalized}\n\n"
                "JSON_OUTPUT:"
            )

            out = llm.generate(prompt=prompt, temperature=0.2)

            try:
                parsed = _extract_json_object(out)
            except Exception:
                parsed = {"raw_output": out.strip()}

            result = {
                "skill": "transform.schema_map",
                "status": "success",
                "target_schema": spec["name"],
                "output": parsed,
            }

            if output_format == "markdown":
                result["rendered_markdown"] = _render_markdown(spec["name"], parsed)

            return result

        except Exception as e:
            return {
                "skill": "transform.schema_map",
                "status": "error",
                "error": str(e),
                "target_schema": spec["name"],
            }

    unmapped: list[str] = []
    if spec["name"] == "default":
        structured = _heuristic_default_schema(normalized)
    else:
        structured, unmapped = _heuristic_custom_schema(spec["name"], normalized)

    result = {
        "skill": "transform.schema_map",
        "status": "success",
        "target_schema": spec["name"],
        "output": structured,
    }

    if unmapped:
        result["unmapped"] = unmapped

    if output_format == "markdown":
        result["rendered_markdown"] = _render_markdown(spec["name"], structured)

    return result


def _render_markdown(schema_name: str, payload: Any) -> str:
    if not isinstance(payload, dict):
        return str(payload)

    lines = [f"# Schema: {schema_name}", ""]
    for k, v in payload.items():
        lines.append(f"## {k}")
        if isinstance(v, list):
            if not v:
                lines.append("- ")
            else:
                for item in v:
                    if isinstance(item, dict):
                        rendered = ", ".join([f"{kk}={vv}" for kk, vv in item.items()])
                        lines.append(f"- {rendered}")
                    else:
                        lines.append(f"- {item}")
        elif isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, list):
                    lines.append(f"- **{kk}**:")
                    for sub in vv:
                        lines.append(f"  - {sub}")
                elif isinstance(vv, dict):
                    lines.append(f"- **{kk}**:")
                    for sk, sv in vv.items():
                        lines.append(f"  - **{sk}**: {sv}")
                else:
                    lines.append(f"- **{kk}**: {vv}")
        else:
            lines.append(str(v))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


transform_schema_map = SimpleSkill(
    id="transform.schema_map",
    name="Transform Schema Map",
    description="Transform freeform text into a structured schema (default or custom frameworks)",
    handler=_transform,
)
