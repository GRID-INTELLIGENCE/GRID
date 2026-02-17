# ContextRefiner

Lightweight helper for cleaning up AI / assistant text **before** pasting it into
code, commit messages, or docs.

The goal is simple: reduce pronouns and tighten references so that text makes
sense **outside** the original chat window.

---

## Why this exists

Cross-environment workflows (chat → editor → terminal → docs) often break
context:

- A response says `the current test results show me the api is fine`.
- In a commit message or code comment, that becomes unclear:
  - Who is "me"?
  - Which tests?
  - Which API?

`context_refiner.py` does a first-pass clean-up so the same line turns into
something like:

> the current test suite currently indicates the API is fine

Not perfect English, but:

- No pronouns.
- Clear anchor (`test suite`, `API`).
- Easier to read in isolation.

---

## Location

- Script path: `e:\grid\context_refiner.py`
- Designed to be run **from the repo root** (`e:\grid`).

---

## Usage

### Direct text

```bash
python context_refiner.py "the current test results show me the api is fine"
```

Example output:

```text
the current test suite currently indicates the API is fine
```

### Pipe from another command

```bash
echo "the current test results show me the api is fine" | python context_refiner.py
```

You can also pipe from a file, another tool, or your clipboard helper.

---

## How it works (prototype)

- Splits text into tokens.
- Drops simple stand-alone pronouns:
  - `i, me, my, mine, we, us, our, ours, it, its, they, them, their, theirs, this, that`.
- Applies a few phrase-level mappings (longest phrase wins):
  - `"test results show" → "test suite currently indicates"`
  - `"test results" → "test suite"`
  - `"tests" → "test suite"`
  - `"result" → "test outcome"`
  - `"api" → "API"`

The rules live in `DEFAULT_CONTEXT_MAP` inside `context_refiner.py` and are
meant to be **edited** as your own patterns emerge.

---

## Extending it

This is intentionally small and readable so you can treat it as a Python
practice file:

- Add more mappings to `DEFAULT_CONTEXT_MAP`.
- Adjust the pronoun list in `PRONOUNS`.
- Swap in a more advanced NLP layer later if you want (spaCy, etc.).

For now, it is a practical "bridge" between AI language and code-facing
language, optimized for your Grid / Silver Surfer workflows.
