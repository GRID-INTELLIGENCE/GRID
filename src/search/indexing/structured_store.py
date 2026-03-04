"""In-memory store for structured field values, powering filters and facets."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from ..models import FieldSchema, FieldType, FilterClause, FilterOp, IndexSchema

logger = logging.getLogger(__name__)


class StructuredFieldIndex:
    """Stores filterable/facetable field values for fast set-based filtering.

    Each field maintains a mapping of value -> set[doc_id], enabling O(1) lookups
    for equality filters and efficient range scans for ordered types.
    """

    def __init__(self, schema: IndexSchema) -> None:
        self.schema = schema
        self._field_data: dict[str, dict[str, Any]] = {}
        self._doc_fields: dict[str, dict[str, Any]] = {}

        for field_name, field_schema in schema.fields.items():
            if field_schema.filterable or field_schema.facetable:
                self._field_data[field_name] = defaultdict(set)

    def add(self, doc_id: str, fields: dict[str, Any]) -> None:
        self._doc_fields[doc_id] = {}
        for field_name, value in fields.items():
            if field_name not in self._field_data:
                continue
            normalized = self._normalize(field_name, value)
            if normalized is None:
                continue
            self._field_data[field_name][normalized].add(doc_id)
            self._doc_fields[doc_id][field_name] = normalized

    def remove(self, doc_id: str) -> None:
        stored = self._doc_fields.pop(doc_id, {})
        for field_name, value in stored.items():
            bucket = self._field_data.get(field_name, {})
            if value in bucket:
                bucket[value].discard(doc_id)
                if not bucket[value]:
                    del bucket[value]

    def filter(self, clauses: list[FilterClause]) -> set[str]:
        """Return doc IDs matching ALL filter clauses (intersection)."""
        if not clauses:
            return set(self._doc_fields.keys())

        result: set[str] | None = None
        for clause in clauses:
            matching = self._apply_clause(clause)
            result = matching if result is None else result & matching
            if not result:
                return set()
        return result or set()

    def get_field_values(self, field_name: str, doc_ids: set[str] | None = None) -> dict[Any, int]:
        """Return value -> count for a field, optionally scoped to a doc set."""
        bucket = self._field_data.get(field_name, {})
        counts: dict[Any, int] = {}
        for value, ids in bucket.items():
            scoped = ids & doc_ids if doc_ids is not None else ids
            if scoped:
                counts[value] = len(scoped)
        return counts

    def get_numeric_values(self, field_name: str, doc_ids: set[str] | None = None) -> list[float]:
        """Return all numeric values for a field, scoped to a doc set."""
        values: list[float] = []
        for doc_id, fields in self._doc_fields.items():
            if doc_ids is not None and doc_id not in doc_ids:
                continue
            if field_name in fields:
                try:
                    values.append(float(fields[field_name]))
                except (TypeError, ValueError):
                    continue
        return values

    def doc_count(self) -> int:
        return len(self._doc_fields)

    def _apply_clause(self, clause: FilterClause) -> set[str]:
        bucket = self._field_data.get(clause.field, {})
        if not bucket:
            return set()

        op = clause.op

        if op == FilterOp.EQ:
            normalized = self._normalize(clause.field, clause.value)
            return set(bucket.get(normalized, set()))

        if op == FilterOp.NEQ:
            normalized = self._normalize(clause.field, clause.value)
            excluded = bucket.get(normalized, set())
            return set(self._doc_fields.keys()) - excluded

        if op == FilterOp.IN:
            target = clause.value if isinstance(clause.value, list) else [clause.value]
            result: set[str] = set()
            for v in target:
                normalized = self._normalize(clause.field, v)
                result |= bucket.get(normalized, set())
            return result

        return self._range_filter(clause.field, op, clause.value)

    def _range_filter(self, field_name: str, op: FilterOp, target: Any) -> set[str]:
        try:
            target_num = float(target)
        except (TypeError, ValueError):
            return set()

        result: set[str] = set()
        for doc_id, fields in self._doc_fields.items():
            raw = fields.get(field_name)
            if raw is None:
                continue
            try:
                doc_val = float(raw)
            except (TypeError, ValueError):
                continue

            match = False
            if op == FilterOp.GT:
                match = doc_val > target_num
            elif op == FilterOp.GTE:
                match = doc_val >= target_num
            elif op == FilterOp.LT:
                match = doc_val < target_num
            elif op == FilterOp.LTE:
                match = doc_val <= target_num

            if match:
                result.add(doc_id)
        return result

    def _normalize(self, field_name: str, value: Any) -> Any:
        field_schema = self.schema.fields.get(field_name)
        if field_schema is None:
            return value

        try:
            if field_schema.type == FieldType.KEYWORD:
                return str(value).lower().strip()
            if field_schema.type == FieldType.INTEGER:
                return int(value)
            if field_schema.type == FieldType.FLOAT:
                return float(value)
            if field_schema.type == FieldType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    normalized = value.strip().lower()
                    if normalized in {"true", "1", "yes", "y", "on"}:
                        return True
                    if normalized in {"false", "0", "no", "n", "off"}:
                        return False
                    return None
                if isinstance(value, (int, float)):
                    return bool(value)
                return None
            if field_schema.type == FieldType.DATETIME:
                if isinstance(value, datetime):
                    return value.isoformat()
                return str(value)
            return str(value)
        except (TypeError, ValueError):
            logger.warning("Cannot normalize %s=%r for field type %s", field_name, value, field_schema.type)
            return None
