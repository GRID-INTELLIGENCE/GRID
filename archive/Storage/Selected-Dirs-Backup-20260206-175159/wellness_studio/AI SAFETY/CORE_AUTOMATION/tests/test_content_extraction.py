"""
Comprehensive Testing Module
Tests for content extraction, PDF parsing, and caching functionality
"""
import unittest
import sys
import os
import importlib.util

# Load live_network_monitor_v3 module
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "live_network_monitor_v3",
    os.path.join(script_dir, "live_network_monitor_v3.py")
)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load live_network_monitor_v3 from {script_dir}")
live_network_monitor_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live_network_monitor_v3)

class TestContentExtraction(unittest.TestCase):
    """Test content extraction functionality"""

    def setUp(self):
        self.html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <main>
                    <h1>Main Content</h1>
                    <p>This is the main content area.</p>
                </main>
                <article>
                    <h2>Article Content</h2>
                    <p>This is an article section.</p>
                </article>
            </body>
        </html>
        """

    def test_extract_text_from_html(self):
        """Test HTML text extraction"""
        text = live_network_monitor_v3.extract_text_from_html(self.html_content)
        self.assertIn("Main Content", text)
        self.assertIn("Article Content", text)
        self.assertNotIn("<", text)
        self.assertNotIn(">", text)

    def test_content_hash_generation(self):
        """Test content hash generation"""
        content = "test content for hashing"
        hash1 = live_network_monitor_v3.get_content_hash(content)
        hash2 = live_network_monitor_v3.get_content_hash(content)
        self.assertEqual(hash1, hash2)

        different_content = "different content"
        hash3 = live_network_monitor_v3.get_content_hash(different_content)
        self.assertNotEqual(hash1, hash3)

class TestCaching(unittest.TestCase):
    """Test caching functionality"""

    def setUp(self):
        """Clear cache before each test"""
        if hasattr(live_network_monitor_v3, '_content_cache'):
            live_network_monitor_v3._content_cache.clear()

    def test_cache_storage_and_retrieval(self):
        """Test caching and retrieval"""
        url = "https://example.com/test"
        content = "test content for caching"

        # Store content
        live_network_monitor_v3.set_cached_content(url, content)

        # Retrieve content
        cached = live_network_monitor_v3.get_cached_content(url)
        self.assertEqual(cached, content)

    def test_is_content_cached(self):
        """Test cache hit detection"""
        url = "https://example.com/test"

        # Initially not cached
        self.assertFalse(live_network_monitor_v3.is_content_cached(url))

        # Cache content
        live_network_monitor_v3.set_cached_content(url, "test content")

        # Now cached
        self.assertTrue(live_network_monitor_v3.is_content_cached(url))

if __name__ == "__main__":
    unittest.main()
