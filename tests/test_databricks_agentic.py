"""Tests for Databricks agentic integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.mothership.db.models_agentic import AgenticCase
from application.mothership.repositories.agentic import AgenticRepository


@pytest.fixture
def mock_session():
    """Create mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create repository instance."""
    return AgenticRepository(session=mock_session)


@pytest.mark.asyncio
async def test_create_case(repository, mock_session):
    """Test creating a case."""
    # Mock the query result
    from sqlalchemy.engine import Result

    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    case = await repository.create_case(case_id="TEST-001", raw_input="Test input", user_id="user123")

    assert case.case_id == "TEST-001"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_case(repository, mock_session):
    """Test getting a case."""
    # Mock case
    mock_case = AgenticCase(case_id="TEST-001", raw_input="Test input", status="created")

    # Mock the query result
    from sqlalchemy.engine import Result

    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = mock_case
    mock_session.execute.return_value = mock_result

    case = await repository.get_case("TEST-001")

    assert case is not None
    assert case.case_id == "TEST-001"


@pytest.mark.asyncio
async def test_update_case_status(repository, mock_session):
    """Test updating case status."""
    # Mock existing case
    mock_case = AgenticCase(case_id="TEST-001", raw_input="Test input", status="created")

    # Mock the query result
    from sqlalchemy.engine import Result

    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = mock_case
    mock_session.execute.return_value = mock_result

    updated = await repository.update_case_status(
        case_id="TEST-001", status="categorized", category="testing", priority="high"
    )

    assert updated is not None
    assert updated.status == "categorized"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_find_similar_cases(repository, mock_session):
    """Test finding similar cases."""
    # Mock cases
    mock_cases = [
        AgenticCase(case_id="TEST-001", category="testing", raw_input="test"),
        AgenticCase(case_id="TEST-002", category="testing", raw_input="test"),
    ]

    # Mock the query result
    from sqlalchemy.engine import Result

    mock_result = MagicMock(spec=Result)
    mock_result.scalars.return_value.all.return_value = mock_cases
    mock_session.execute.return_value = mock_result

    similar = await repository.find_similar_cases(category="testing", keywords=["test"], limit=10)

    assert len(similar) == 2


@pytest.mark.asyncio
async def test_get_agent_experience(repository, mock_session):
    """Test getting agent experience."""
    # Mock query results
    from sqlalchemy.engine import Result

    # Total cases
    total_result = MagicMock(spec=Result)
    total_result.scalar.return_value = 100
    mock_session.execute.return_value = total_result

    # Success count
    success_result = MagicMock(spec=Result)
    success_result.scalar.return_value = 85

    # Category distribution
    cat_result = MagicMock(spec=Result)
    cat_result.all.return_value = [("testing", 25), ("architecture", 20)]

    # Mock execute to return different results based on query
    def execute_side_effect(query):
        if "count" in str(query) and "outcome" not in str(query):
            return total_result
        elif "outcome" in str(query):
            return success_result
        elif "group_by" in str(query):
            return cat_result
        return total_result

    mock_session.execute.side_effect = execute_side_effect

    experience = await repository.get_agent_experience()

    assert experience["total_cases"] == 100
    assert experience["success_rate"] == 0.85
    assert "category_distribution" in experience
