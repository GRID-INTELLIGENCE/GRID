"""Tests for version scoring and tier assignment."""


from coinbase.version_scoring import VersionMetrics, VersionScorer


def test_calculate_version_score_gold_tier():
    """Test version score calculation for gold tier (3.5)."""
    scorer = VersionScorer()

    metrics = VersionMetrics(
        coherence_accumulation=0.95,
        evolution_count=80,
        pattern_emergence_rate=0.9,
        operation_success_rate=0.95,
        avg_confidence=0.9,
        skill_retrieval_score=0.85,
        resource_efficiency=0.8,
        error_recovery_rate=0.85,
    )

    score, version = scorer.calculate_version_score(metrics)

    assert score >= 0.85
    assert version == "3.5"


def test_calculate_version_score_silver_tier():
    """Test version score calculation for silver tier (3.0)."""
    scorer = VersionScorer()

    metrics = VersionMetrics(
        coherence_accumulation=0.75,
        evolution_count=70,
        pattern_emergence_rate=0.75,
        operation_success_rate=0.8,
        avg_confidence=0.75,
        skill_retrieval_score=0.75,
        resource_efficiency=0.75,
        error_recovery_rate=0.75,
    )

    score, version = scorer.calculate_version_score(metrics)

    assert 0.70 <= score < 0.85
    assert version == "3.0"


def test_calculate_version_score_bronze_tier():
    """Test version score calculation for bronze tier (2.0)."""
    scorer = VersionScorer()

    metrics = VersionMetrics(
        coherence_accumulation=0.55,
        evolution_count=40,
        pattern_emergence_rate=0.55,
        operation_success_rate=0.55,
        avg_confidence=0.55,
        skill_retrieval_score=0.55,
        resource_efficiency=0.55,
        error_recovery_rate=0.55,
    )

    score, version = scorer.calculate_version_score(metrics)

    assert 0.50 <= score < 0.70
    assert version == "2.0"


def test_calculate_version_score_basic_tier():
    """Test version score calculation for basic tier (1.0)."""
    scorer = VersionScorer()

    metrics = VersionMetrics(
        coherence_accumulation=0.2,
        evolution_count=10,
        pattern_emergence_rate=0.2,
        operation_success_rate=0.3,
        avg_confidence=0.3,
        skill_retrieval_score=0.3,
        resource_efficiency=0.3,
        error_recovery_rate=0.3,
    )

    score, version = scorer.calculate_version_score(metrics)

    assert score < 0.50
    assert version == "1.0"


def test_record_version_checkpoint():
    """Test recording version checkpoints."""
    scorer = VersionScorer()

    scorer.record_version_checkpoint(batch=1, score=0.80, version="3.0")
    scorer.record_version_checkpoint(batch=2, score=0.85, version="3.5")
    scorer.record_version_checkpoint(batch=3, score=0.90, version="3.5")

    history = scorer.get_version_history()

    assert len(history) == 3
    assert history[0]["batch"] == 1
    assert history[1]["score"] == 0.85
    assert history[2]["version"] == "3.5"


def test_validate_momentum_positive():
    """Test momentum validation with positive trend."""
    scorer = VersionScorer()

    scorer.record_version_checkpoint(batch=1, score=0.70, version="3.0")
    scorer.record_version_checkpoint(batch=2, score=0.80, version="3.0")
    scorer.record_version_checkpoint(batch=3, score=0.85, version="3.5")

    assert scorer.validate_momentum() is True


def test_validate_momentum_negative():
    """Test momentum validation with negative trend."""
    scorer = VersionScorer()

    scorer.record_version_checkpoint(batch=1, score=0.90, version="3.5")
    scorer.record_version_checkpoint(batch=2, score=0.70, version="3.0")
    scorer.record_version_checkpoint(batch=3, score=0.60, version="2.0")

    assert scorer.validate_momentum() is False


def test_validate_momentum_single_checkpoint():
    """Test momentum validation with single checkpoint."""
    scorer = VersionScorer()

    scorer.record_version_checkpoint(batch=1, score=0.80, version="3.0")

    assert scorer.validate_momentum() is True


def test_validate_momentum_empty():
    """Test momentum validation with no checkpoints."""
    scorer = VersionScorer()

    assert scorer.validate_momentum() is True


def test_get_latest_version():
    """Test getting latest version from history."""
    scorer = VersionScorer()

    assert scorer.get_latest_version() is None

    scorer.record_version_checkpoint(batch=1, score=0.80, version="3.0")
    scorer.record_version_checkpoint(batch=2, score=0.85, version="3.5")

    assert scorer.get_latest_version() == "3.5"
