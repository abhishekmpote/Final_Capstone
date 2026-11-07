"""Tests for recursive, source-preserving text chunking."""

import unittest

from backend.utils.text_chunker import split_text


class TextChunkerTests(unittest.TestCase):
    def test_chunks_respect_size_and_preserve_punctuation(self) -> None:
        text = "One sentence. Two sentences. A third sentence."
        chunks = split_text(text, chunk_size=18, overlap=4)

        self.assertTrue(chunks)
        self.assertTrue(all(len(chunk) <= 18 for chunk in chunks))
        self.assertIn("One sentence.", " ".join(chunks))
        self.assertIn("Two sentences.", " ".join(chunks))
        self.assertIn("A third sentence.", " ".join(chunks))

    def test_long_text_has_overlap_and_no_oversized_chunks(self) -> None:
        text = "word " * 50
        chunks = split_text(text, chunk_size=20, overlap=3)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 20 for chunk in chunks))
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_overlap_preserves_complete_words_at_chunk_boundaries(self) -> None:
        chunks = split_text(
            "alpha bravo charlie delta echo foxtrot", chunk_size=22, overlap=6
        )

        self.assertEqual(
            chunks,
            ["alpha bravo charlie", "charlie delta echo", "delta echo foxtrot"],
        )

    def test_empty_text_returns_no_chunks(self) -> None:
        self.assertEqual(split_text(" \n\t ", chunk_size=20, overlap=2), [])

    def test_invalid_overlap_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            split_text("text", chunk_size=10, overlap=10)


if __name__ == "__main__":
    unittest.main()
