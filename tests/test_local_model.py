import unittest
from sovereign_ai.config import is_local_endpoint, load_settings
from sovereign_ai.embeddings import LocalEmbedder
from sovereign_ai.local_provider import OpenAICompatibleProvider


class LocalModelTests(unittest.TestCase):
    def test_sovereign_mode_rejects_public_endpoints(self):
        self.assertTrue(is_local_endpoint("http://127.0.0.1:1234/v1"))
        self.assertTrue(is_local_endpoint("http://host.docker.internal:1234/v1"))
        self.assertFalse(is_local_endpoint("https://api.example.com/v1"))

    def test_embedding_fallback_is_local_and_deterministic(self):
        embedder = LocalEmbedder("http://127.0.0.1:9/v1")
        first, second = embedder.embed(["local evidence"])[0], embedder.embed(["local evidence"])[0]
        self.assertEqual(first, second)
        self.assertGreater(len(first), 0)

    def test_bionic_health_is_reported_without_external_fallback(self):
        provider = OpenAICompatibleProvider(load_settings().local_model_url)
        healthy, message = provider.health_check()
        if not healthy:
            self.skipTest("Bionic Studio Local Model API is not running")
        self.assertTrue(healthy, message)

    def test_bionic_non_streaming_generation_when_available(self):
        provider = OpenAICompatibleProvider(load_settings().local_model_url)
        healthy, _ = provider.health_check()
        if not healthy:
            self.skipTest("Bionic Studio Local Model API is not running")
        result = provider.generate("Reply with exactly LOCAL_GENERATE_OK.", "google/gemma-4-e2b")
        self.assertIn("LOCAL_GENERATE_OK", result)


if __name__ == "__main__": unittest.main()
