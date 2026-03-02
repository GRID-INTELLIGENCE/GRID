"""Query parser: extracts field-qualified filters from raw query strings."""

from __future__ import annotations

import re

from ..models import FieldType, FilterClause, FilterOp, IndexSchema, SearchQuery

# Sanitization limits and patterns (aligned with guardrail sanitize_tool)
MAX_QUERY_LENGTH = 10_000
DANGEROUS_PATTERNS = [
    re.compile(r"[,;{}\\]"),
    re.compile(r"(?i)(?:drop|delete|truncate|insert|update)\s+\w+"),
    re.compile(r"(?i)javascript\s*:"),
    re.compile(r"<script"),
    re.compile(r"\$\{|%\s*\{"),
]


def sanitize(raw: str) -> tuple[bool, str | None]:
    """Validate and sanitize query text. Returns (valid, error_message)."""
    if not isinstance(raw, str):
        return False, "Query must be a string"
    if len(raw) > MAX_QUERY_LENGTH:
        return False, f"Query exceeds max length ({MAX_QUERY_LENGTH})"
    for pat in DANGEROUS_PATTERNS:
        if pat.search(raw):
            return False, "Query contains disallowed patterns"
    return True, None


FILTER_PATTERN = re.compile(
    r"""
    (\w+)                   # field name
    :                       # separator
    (>=|<=|>|<|!=|=)?       # optional operator
    (?:"([^"]+)"|(\S+))    # quoted or unquoted value
    """,
    re.VERBOSE,
)

OP_MAP: dict[str | None, FilterOp] = {
    None: FilterOp.EQ,
    "=": FilterOp.EQ,
    "!=": FilterOp.NEQ,
    ">": FilterOp.GT,
    ">=": FilterOp.GTE,
    "<": FilterOp.LT,
    "<=": FilterOp.LTE,
}


class QueryParser:
    """Parses raw query strings into structured SearchQuery objects.

    Recognises field-qualified filters like ``category:electronics price:>100``
    and separates them from the free-text portion.
    """

    def __init__(self, schema: IndexSchema) -> None:
        self.schema = schema
        self._filterable = set(schema.filterable_fields().keys())

    def parse(
        self,
        raw: str,
        page: int = 1,
        size: int = 10,
        facet_fields: list[str] | None = None,
    ) -> SearchQuery:
        filters: list[FilterClause] = []
        remaining = raw

        for match in FILTER_PATTERN.finditer(raw):
            field_name = match.group(1)
            if field_name not in self._filterable:
                continue

            op_str = match.group(2)
            value = match.group(3) or match.group(4)
            op = OP_MAP.get(op_str, FilterOp.EQ)

            value = self._coerce_value(field_name, value)
            filters.append(FilterClause(field=field_name, op=op, value=value))
            remaining = remaining.replace(match.group(0), "", 1)

        free_text = " ".join(remaining.strip().split())

        return SearchQuery(
            raw_text=raw,
            text=free_text,
            filters=filters,
            facet_fields=facet_fields or [],
            page=page,
            size=size,
        )

    def _coerce_value(self, field_name: str, value: str) -> str | int | float | bool:
        field_schema = self.schema.fields.get(field_name)
        if field_schema is None:
            return value

        if field_schema.type == FieldType.INTEGER:
            try:
                return int(value)
            except ValueError:
                return value
        if field_schema.type == FieldType.FLOAT:
            try:
                return float(value)
            except ValueError:
                return value
        if field_schema.type == FieldType.BOOLEAN:
            return value.lower() in ("true", "1", "yes")
        return value
