"""Facet aggregator: computes value counts and histograms scoped to a result set."""

from __future__ import annotations

from collections import Counter

from ..indexing.structured_store import StructuredFieldIndex
from ..models import FacetResult, FacetValue, FieldType, IndexSchema


class FacetAggregator:
    """Computes facet counts for keyword, numeric, and boolean fields.

    All counts are scoped to the current result set (post-filter, post-rank)
    so facet values reflect what the user would see after applying their query.
    """

    def __init__(
        self,
        schema: IndexSchema,
        structured_index: StructuredFieldIndex,
        default_max_values: int = 20,
        default_histogram_buckets: int = 10,
    ) -> None:
        self.schema = schema
        self.structured_index = structured_index
        self.default_max_values = default_max_values
        self.default_histogram_buckets = default_histogram_buckets

    def aggregate(
        self,
        result_doc_ids: set[str],
        facet_fields: list[str],
        max_values: int | None = None,
        histogram_buckets: int | None = None,
    ) -> dict[str, FacetResult]:
        max_values = max_values or self.default_max_values
        histogram_buckets = histogram_buckets or self.default_histogram_buckets
        facets: dict[str, FacetResult] = {}

        for field_name in facet_fields:
            field_schema = self.schema.fields.get(field_name)
            if field_schema is None or not field_schema.facetable:
                continue

            if field_schema.type in (FieldType.FLOAT, FieldType.INTEGER):
                facets[field_name] = self._numeric_histogram(
                    field_name,
                    result_doc_ids,
                    histogram_buckets,
                )
            elif field_schema.type == FieldType.BOOLEAN:
                facets[field_name] = self._boolean_facet(field_name, result_doc_ids)
            else:
                facets[field_name] = self._keyword_facet(
                    field_name,
                    result_doc_ids,
                    max_values,
                )

        return facets

    def _keyword_facet(self, field_name: str, doc_ids: set[str], max_values: int) -> FacetResult:
        value_counts = self.structured_index.get_field_values(field_name, doc_ids)
        sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:max_values]
        return FacetResult(
            field=field_name,
            values=[FacetValue(value=v, count=c) for v, c in sorted_values],
        )

    def _boolean_facet(self, field_name: str, doc_ids: set[str]) -> FacetResult:
        value_counts = self.structured_index.get_field_values(field_name, doc_ids)
        return FacetResult(
            field=field_name,
            values=[FacetValue(value=v, count=c) for v, c in value_counts.items()],
        )

    def _numeric_histogram(self, field_name: str, doc_ids: set[str], n_buckets: int) -> FacetResult:
        values = self.structured_index.get_numeric_values(field_name, doc_ids)
        if not values:
            return FacetResult(field=field_name, values=[])

        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            return FacetResult(
                field=field_name,
                values=[FacetValue(value=min_val, count=len(values))],
            )

        bucket_width = (max_val - min_val) / n_buckets
        bucket_counts: Counter[int] = Counter()
        for v in values:
            bucket_idx = min(int((v - min_val) / bucket_width), n_buckets - 1)
            bucket_counts[bucket_idx] += 1

        facet_values: list[FacetValue] = []
        for i in range(n_buckets):
            bucket_start = round(min_val + i * bucket_width, 2)
            bucket_end = round(min_val + (i + 1) * bucket_width, 2)
            count = bucket_counts.get(i, 0)
            if count > 0:
                facet_values.append(FacetValue(value=f"{bucket_start}-{bucket_end}", count=count))

        return FacetResult(field=field_name, values=facet_values)
