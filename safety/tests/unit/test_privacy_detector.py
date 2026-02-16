import pytest

from safety.privacy.detector import AsyncPIIDetector


@pytest.fixture
def detector():
    return AsyncPIIDetector(enable_cache=False)


@pytest.mark.asyncio
async def test_email_detection(detector):
    text = "Contact me at test@example.com for more info."
    results = await detector.detect_async(text)

    assert len(results) == 1
    assert results[0].pii_type == "EMAIL"
    assert results[0].value == "test@example.com"


@pytest.mark.asyncio
async def test_phone_detection(detector):
    text = "Call 555-555-0123 immediately."
    results = await detector.detect_async(text)

    assert len(results) == 1
    # Note: Our regex might be strict or loose, let's verify it matches
    assert results[0].pii_type == "PHONE"


@pytest.mark.asyncio
async def test_multiple_detections(detector):
    text = "Email: a@b.com, Phone: 555-555-0199"
    results = await detector.detect_async(text)

    assert len(results) == 2
    types = {r.pii_type for r in results}
    assert "EMAIL" in types
    assert "PHONE" in types


@pytest.mark.asyncio
async def test_no_pii(detector):
    text = "Hello world, this is a safe string."
    results = await detector.detect_async(text)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_batch_processing(detector):
    texts = ["My email is a@b.com", "No secrets here", "Call 555-555-0199"]
    results = await detector.detect_batch(texts)

    assert len(results) == 3
    assert len(results[0]) == 1  # 1 email
    assert len(results[1]) == 0  # 0 pii
    assert len(results[2]) >= 1  # 1 phone
