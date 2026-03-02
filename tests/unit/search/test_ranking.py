"""Tests for search.ranking (features, ltr_model, scorer)."""

import numpy as np
import pytest

from search.models import Document, FieldSchema, FieldType, IndexSchema, ScoredCandidate
from search.ranking.features import FEATURE_NAMES, FeatureExtractor
from search.ranking.ltr_model import LTRModel


@pytest.fixture
def schema():
    return IndexSchema(
        name="test",
        fields={
            "title": FieldSchema(type=FieldType.TEXT, searchable=True, weight=2.0),
            "body": FieldSchema(type=FieldType.TEXT, searchable=True),
            "views": FieldSchema(type=FieldType.INTEGER, filterable=True),
        },
    )


class TestFeatureExtractor:
    def test_produces_correct_dimensions(self, schema):
        extractor = FeatureExtractor(schema)
        doc = Document(id="d1", fields={"title": "hello world", "body": "test", "views": 100})
        candidate = ScoredCandidate(doc_id="d1", score=0.5, source="fusion")
        features = extractor.extract("hello", doc, candidate, {"d1": 2.5}, {"d1": 0.8}, 0)
        assert features.shape == (len(FEATURE_NAMES),)
        assert features.dtype == np.float32

    def test_bm25_and_vector_scores(self, schema):
        extractor = FeatureExtractor(schema)
        doc = Document(id="d1", fields={"title": "x", "body": "y", "views": 0})
        candidate = ScoredCandidate(doc_id="d1")
        features = extractor.extract("x", doc, candidate, {"d1": 3.0}, {"d1": 0.7}, 5)
        assert features[0] == pytest.approx(3.0)
        assert features[1] == pytest.approx(0.7)
        assert features[2] == pytest.approx(5.0)

    def test_popularity_from_views(self, schema):
        extractor = FeatureExtractor(schema)
        doc = Document(id="d1", fields={"title": "x", "body": "y", "views": 42})
        candidate = ScoredCandidate(doc_id="d1")
        features = extractor.extract("x", doc, candidate, {}, {}, 0)
        assert features[7] == pytest.approx(42.0)

    def test_batch_extraction(self, schema):
        extractor = FeatureExtractor(schema)
        docs = [
            Document(id="d1", fields={"title": "a", "body": "b", "views": 0}),
            Document(id="d2", fields={"title": "c", "body": "d", "views": 0}),
        ]
        candidates = [ScoredCandidate(doc_id="d1"), ScoredCandidate(doc_id="d2")]
        matrix = extractor.extract_batch("test", docs, candidates, {}, {})
        assert matrix.shape == (2, len(FEATURE_NAMES))


class TestLTRModel:
    def test_train_predict_roundtrip(self):
        model = LTRModel(n_estimators=10, max_depth=2)
        rng = np.random.default_rng(42)
        features = rng.standard_normal((50, 8)).astype(np.float32)
        labels = rng.standard_normal(50).astype(np.float32)
        metrics = model.train(features, labels)
        assert "train_mse" in metrics
        assert model.is_fitted

        preds = model.predict(features)
        assert preds.shape == (50,)

    def test_predict_before_train_raises(self):
        model = LTRModel()
        with pytest.raises(RuntimeError, match="not been trained"):
            model.predict(np.zeros((1, 8)))

    def test_feature_importances(self):
        model = LTRModel(n_estimators=10)
        rng = np.random.default_rng(0)
        features = rng.standard_normal((30, 8)).astype(np.float32)
        labels = rng.standard_normal(30).astype(np.float32)
        model.train(features, labels)
        importances = model.feature_importances()
        assert len(importances) == len(FEATURE_NAMES)
        assert all(isinstance(v, float) for v in importances.values())

    def test_save_load(self, tmp_path):
        model = LTRModel(n_estimators=10)
        rng = np.random.default_rng(1)
        features = rng.standard_normal((20, 8)).astype(np.float32)
        labels = rng.standard_normal(20).astype(np.float32)
        model.train(features, labels)

        path = tmp_path / "model.joblib"
        model.save(path)

        model2 = LTRModel()
        model2.load(path)
        assert model2.is_fitted
        preds = model2.predict(features)
        assert preds.shape == (20,)
