"""
Integration tests for Activity Resonance API router.

Tests REST endpoints with TestClient, request/response validation, and error handling.
"""

from fastapi import status
from fastapi.testclient import TestClient


class TestProcessActivity:
    """Test POST /api/v1/resonance/process endpoint."""

    def test_process_activity_success(self, client: TestClient) -> None:
        """Test successful activity processing."""
        response = client.post(
            "/api/v1/resonance/process",
            json={
                "query": "create a new service",
                "activity_type": "code",
                "context": {"urgency": True},
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "activity_id" in data
        assert data["state"] in ["idle", "context_loading", "path_triaging", "active", "feedback", "complete"]
        assert "urgency" in data
        assert "message" in data

    def test_process_activity_minimal(self, client: TestClient) -> None:
        """Test activity processing with minimal fields."""
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test query"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "activity_id" in data

    def test_process_activity_invalid_query(self, client: TestClient) -> None:
        """Test activity processing with invalid query."""
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": ""},  # Empty query
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestGetContext:
    """Test GET /api/v1/resonance/context endpoint."""

    def test_get_context_success(self, client: TestClient) -> None:
        """Test successful context retrieval."""
        response = client.get(
            "/api/v1/resonance/context",
            params={
                "query": "test query",
                "context_type": "code",
                "max_length": 200,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "content" in data
        assert "source" in data
        assert "metrics" in data
        assert "timestamp" in data
        assert "relevance_score" in data

    def test_get_context_minimal(self, client: TestClient) -> None:
        """Test context retrieval with minimal parameters."""
        response = client.get(
            "/api/v1/resonance/context",
            params={"query": "test query"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "content" in data

    def test_get_context_missing_query(self, client: TestClient) -> None:
        """Test context retrieval without query parameter."""
        response = client.get("/api/v1/resonance/context/query")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestGetPaths:
    """Test GET /api/v1/resonance/paths endpoint."""

    def test_get_paths_success(self, client: TestClient) -> None:
        """Test successful path triage retrieval."""
        response = client.get(
            "/api/v1/resonance/paths",
            params={
                "goal": "implement feature",
                "max_options": 4,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "goal" in data
        assert "options" in data
        assert "total_options" in data
        assert "glimpse_summary" in data
        assert len(data["options"]) > 0

    def test_get_paths_minimal(self, client: TestClient) -> None:
        """Test path triage with minimal parameters."""
        response = client.get(
            "/api/v1/resonance/paths",
            params={"goal": "test goal"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "options" in data

    def test_get_paths_missing_goal(self, client: TestClient) -> None:
        """Test path triage without goal parameter."""
        response = client.get("/api/v1/resonance/paths")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestGetEnvelope:
    """Test GET /api/v1/resonance/envelope/{activity_id} endpoint."""

    def test_get_envelope_success(self, client: TestClient, sample_activity_id: str) -> None:
        """Test successful envelope metrics retrieval."""
        response = client.get(f"/api/v1/resonance/envelope/{sample_activity_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "phase" in data
        assert "amplitude" in data
        assert "velocity" in data
        assert "time_in_phase" in data
        assert "total_time" in data
        assert "peak_amplitude" in data

    def test_get_envelope_not_found(self, client: TestClient) -> None:
        """Test envelope retrieval for non-existent activity."""
        response = client.get("/api/v1/resonance/envelope/non-existent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCompleteActivity:
    """Test POST /api/v1/resonance/complete/{activity_id} endpoint."""

    def test_complete_activity_success(self, client: TestClient, sample_activity_id: str) -> None:
        """Test successful activity completion."""
        response = client.post(f"/api/v1/resonance/complete/{sample_activity_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["activity_id"] == sample_activity_id
        assert data["completed"] is True
        assert "message" in data
        assert "timestamp" in data

    def test_complete_activity_not_found(self, client: TestClient) -> None:
        """Test completing non-existent activity."""
        response = client.post("/api/v1/resonance/complete/non-existent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetEvents:
    """Test GET /api/v1/resonance/events/{activity_id} endpoint."""

    def test_get_events_success(self, client: TestClient, sample_activity_id: str) -> None:
        """Test successful events retrieval."""
        response = client.get(
            f"/api/v1/resonance/events/{sample_activity_id}",
            params={"limit": 10},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["activity_id"] == sample_activity_id
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)

    def test_get_events_with_limit(self, client: TestClient, sample_activity_id: str) -> None:
        """Test events retrieval with limit."""
        response = client.get(
            f"/api/v1/resonance/events/{sample_activity_id}",
            params={"limit": 5},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) <= 5

    def test_get_events_empty(self, client: TestClient) -> None:
        """Test events retrieval for activity with no events."""
        # Create activity but don't process it
        response = client.post(
            "/api/v1/resonance/process",
            json={"query": "test"},
        )
        activity_id = response.json()["activity_id"]

        # Get events (should be empty or minimal)
        response = client.get(f"/api/v1/resonance/events/{activity_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)


class TestDefinitiveStep:
    """Test POST /api/v1/resonance/definitive endpoint."""

    def test_definitive_step_success(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/resonance/definitive",
            json={
                "query": "Where do these features connect and what is the main function of this update?",
                "activity_type": "general",
                "progress": 0.65,
                "target_schema": "context_engineering",
                "use_rag": False,
                "use_llm": False,
                "max_chars": 200,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "activity_id" in data
        assert "summary" in data
        assert "canvas_before" in data
        assert "canvas_after" in data
        assert "faq" in data and isinstance(data["faq"], list)
        assert "use_cases" in data and isinstance(data["use_cases"], list)
        assert "api_mechanics" in data and isinstance(data["api_mechanics"], list)
        assert "structured" in data and isinstance(data["structured"], dict)

    def test_definitive_step_progress_zero(self, client: TestClient) -> None:
        """Test definitive step with progress=0.0 (edge case: start of process)."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={
                "query": "Test at zero progress",
                "progress": 0.0,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["progress"] == 0.0
        assert "activity_id" in data

    def test_definitive_step_progress_one(self, client: TestClient) -> None:
        """Test definitive step with progress=1.0 (edge case: end of process)."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={
                "query": "Test at full progress",
                "progress": 1.0,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["progress"] == 1.0
        assert "activity_id" in data

    def test_definitive_step_minimal_query(self, client: TestClient) -> None:
        """Test definitive step with minimal valid query (1 character)."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={"query": "X"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "activity_id" in data

    def test_definitive_step_empty_query_rejected(self, client: TestClient) -> None:
        """Test that empty query is rejected with 422."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={"query": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_definitive_step_long_query(self, client: TestClient) -> None:
        """Test definitive step with a long query (near max limit)."""
        long_query = "A" * 3999  # Just under 4000 char limit
        response = client.post(
            "/api/v1/resonance/definitive",
            json={"query": long_query},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "activity_id" in data

    def test_definitive_step_query_too_long_rejected(self, client: TestClient) -> None:
        """Test that query exceeding max length is rejected with 422."""
        too_long_query = "B" * 4001  # Exceeds 4000 char limit
        response = client.post(
            "/api/v1/resonance/definitive",
            json={"query": too_long_query},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_definitive_step_use_rag_without_index(self, client: TestClient) -> None:
        """Test definitive step with use_rag=true when index may not exist."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={
                "query": "Test RAG enrichment",
                "use_rag": True,
                "use_llm": False,
            },
        )

        # Should succeed even if RAG index is missing (graceful degradation)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "activity_id" in data
        # RAG field may be None or contain error info
        assert "rag" in data

    def test_definitive_step_idempotent_same_response_shape(self, client: TestClient) -> None:
        """Test that repeated identical requests return consistent response shape."""
        payload = {
            "query": "Idempotency test query",
            "activity_type": "general",
            "progress": 0.65,
        }

        response1 = client.post("/api/v1/resonance/definitive", json=payload)
        response2 = client.post("/api/v1/resonance/definitive", json=payload)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        data1 = response1.json()
        data2 = response2.json()

        # Both should have same structure (activity_id will differ)
        assert set(data1.keys()) == set(data2.keys())
        assert data1["progress"] == data2["progress"]
        assert data1["canvas_before"] == data2["canvas_before"]
        assert data1["canvas_after"] == data2["canvas_after"]

    def test_definitive_step_retry_after_failure_simulation(self, client: TestClient) -> None:
        """Test that a valid request succeeds after a previous invalid request."""
        # First: invalid request
        invalid_response = client.post(
            "/api/v1/resonance/definitive",
            json={"query": ""},  # Invalid empty query
        )
        assert invalid_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Then: valid retry
        valid_response = client.post(
            "/api/v1/resonance/definitive",
            json={"query": "Valid retry query"},
        )
        assert valid_response.status_code == status.HTTP_200_OK
        assert "activity_id" in valid_response.json()

    def test_definitive_step_partial_payload(self, client: TestClient) -> None:
        """Test definitive step with only required field (query)."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={"query": "Minimal payload test"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should use defaults
        assert data["progress"] == 0.65  # Default
        assert "activity_id" in data
        assert "summary" in data

    def test_definitive_step_invalid_activity_type_rejected(self, client: TestClient) -> None:
        """Test that invalid activity_type is rejected."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={
                "query": "Test query",
                "activity_type": "invalid_type",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_definitive_step_progress_out_of_range_rejected(self, client: TestClient) -> None:
        """Test that progress outside 0.0-1.0 is rejected."""
        response = client.post(
            "/api/v1/resonance/definitive",
            json={
                "query": "Test query",
                "progress": 1.5,  # Out of range
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_definitive_step_max_chars_boundary(self, client: TestClient) -> None:
        """Test max_chars at boundary values (20 min, 2000 max)."""
        # Min boundary
        response_min = client.post(
            "/api/v1/resonance/definitive",
            json={"query": "Test", "max_chars": 20},
        )
        assert response_min.status_code == status.HTTP_200_OK

        # Max boundary
        response_max = client.post(
            "/api/v1/resonance/definitive",
            json={"query": "Test", "max_chars": 2000},
        )
        assert response_max.status_code == status.HTTP_200_OK

        # Below min
        response_below = client.post(
            "/api/v1/resonance/definitive",
            json={"query": "Test", "max_chars": 19},
        )
        assert response_below.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Above max
        response_above = client.post(
            "/api/v1/resonance/definitive",
            json={"query": "Test", "max_chars": 2001},
        )
        assert response_above.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
