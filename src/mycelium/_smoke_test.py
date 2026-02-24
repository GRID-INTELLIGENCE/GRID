"""Smoke test for Mycelium Instrument — run with: uv run python src/mycelium/_smoke_test.py"""

import sys
sys.path.insert(0, "src")

from mycelium.instrument import Instrument

SAMPLE_TEXT = (
    "Redis is an open-source, in-memory data structure store that serves as a "
    "database, cache, and message broker. It supports various data structures like "
    "strings, hashes, lists, sets, and streams, and provides high performance through "
    "in-memory storage. Redis achieves sub-millisecond latency by keeping all data in "
    "RAM. The persistence options include RDB snapshots and append-only file logging. "
    "Redis Pub/Sub enables real-time messaging between services. Rate limiting can be "
    "implemented using Redis counters with expiration. Redis Cluster provides horizontal "
    "scaling through automatic data partitioning across multiple nodes. The sorted set "
    "data structure is particularly useful for leaderboards and ranking systems."
)


def main() -> None:
    m = Instrument()
    print("=== REPR ===")
    print(repr(m))

    print("\n=== SYNTHESIZE ===")
    result = m.synthesize(SAMPLE_TEXT)
    print("GIST:", result.gist)
    print("HIGHLIGHTS:", [(h.text, h.priority.name) for h in result.highlights[:5]])
    print("PATTERNS:", result.patterns_applied)
    print("COMPRESSION:", round(result.compression_ratio, 3))

    print("\n=== EXPLORE ===")
    nav = m.explore("cache")
    if nav:
        print("PATTERN:", nav.lens.pattern)
        print("ANALOGY:", nav.lens.analogy)
        print("ELI5:", nav.lens.eli5)

    print("\n=== ELI5 ===")
    print(m.eli5("recursion"))

    print("\n=== SET USER (child, playful) ===")
    m.set_user(expertise="child", tone="playful")
    result2 = m.synthesize(SAMPLE_TEXT)
    print("CHILD GIST:", result2.gist)
    print("SCAFFOLDING:", result2.scaffolding_applied)

    print("\n=== KEYWORDS ===")
    kws = m.keywords(SAMPLE_TEXT, top_n=5)
    for kw in kws:
        print(f"  {kw['text']} ({kw['priority']})")

    print("\n=== EXPLAIN ===")
    print(m.explain("mycelium"))

    print("\n=== SENSORY (cognitive) ===")
    info = m.set_sensory("cognitive")
    print(info)

    print("\n=== CONCEPTS (first 8) ===")
    print(m.concepts[:8])

    print("\n=== FEEDBACK LOOP ===")
    m.feedback(too_complex=True)
    result3 = m.synthesize(SAMPLE_TEXT)
    print("AFTER too_complex FEEDBACK, scaffolding:", result3.scaffolding_applied)

    print("\n=== TRY DIFFERENT LENS ===")
    nav2 = m.try_different("cache")
    if nav2:
        print("ALT PATTERN:", nav2.lens.pattern)
        print("ALT ELI5:", nav2.lens.eli5)

    print("\n=== SUMMARIZE (2 sentences) ===")
    print(m.summarize(SAMPLE_TEXT, sentences=2))

    print("\n=== SIMPLIFY ===")
    print(m.simplify(SAMPLE_TEXT))

    print("\nALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
