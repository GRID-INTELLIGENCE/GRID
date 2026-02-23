import pytest
import requests


@pytest.mark.scratch
def test_nomic_v2_limit(text_len):
    url = "http://localhost:11434/api/embeddings"
    data = {"model": "nomic-embed-text-v2-moe:latest", "prompt": "A" * text_len}
    try:
        response = requests.post(url, json=data, timeout=30)
        return response.status_code, response.text[:200]
    except Exception as e:
        return 0, str(e)


print("Starting Nomic V2 stress test...")
for length in [512, 1024, 2048, 4096, 8192]:
    status, body = test_nomic_v2_limit(length)
    print(f"Length {length}: Status {status}, Body: {body}")
