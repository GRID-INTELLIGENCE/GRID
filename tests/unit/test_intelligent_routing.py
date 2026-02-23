from unittest.mock import MagicMock

import pytest

from grid.kernel.routing import HeuristicRouter, PriorityQueue


class TestPriorityQueue:
    def test_priority_queue_ordering(self):
        pq = PriorityQueue()
        pq.put("low", priority=1)
        pq.put("high", priority=10)
        pq.put("medium", priority=5)

        assert pq.get() == "high"
        assert pq.get() == "medium"
        assert pq.get() == "low"
        assert pq.get() is None


class TestHeuristicRouter:
    def test_heuristic_router_logic(self):
        router = HeuristicRouter()
        router.route("task1", priority=1)
        router.route("task2", priority=2)

        assert router.get_next() == "task2"
        assert router.get_next() == "task1"

    def test_pipeline_applies_heuristics(self):
        mock_pipeline = MagicMock()
        router = HeuristicRouter(pipeline=mock_pipeline)

        router.route("item1", priority=10)
        router.route("item2", priority=1)

        router.process_all()

        # Verify call order
        assert mock_pipeline.publish_sync.call_count == 2
        mock_pipeline.publish_sync.assert_any_call("item1")
        mock_pipeline.publish_sync.assert_any_call("item2")
