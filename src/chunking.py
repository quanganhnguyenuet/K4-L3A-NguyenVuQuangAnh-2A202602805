from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = max(1, chunk_size)
        self.overlap = min(max(0, overlap), self.chunk_size - 1)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Keep terminal punctuation with the sentence.  The expression covers
        # the documented separators (". ", "! ", "? ", and ".\n") as
        # well as repeated whitespace after a sentence.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
            if sentence.strip()
        ]

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            chunks.append(" ".join(sentences[start : start + self.max_sentences_per_chunk]))
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return [chunk.strip() for chunk in self._split(text, self.separators) if chunk.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        """Split oversized text, trying each separator from highest priority."""
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator_index = next(
            (
                index
                for index, separator in enumerate(remaining_separators)
                if separator == "" or separator in current_text
            ),
            None,
        )
        if separator_index is None:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[separator_index]
        later_separators = remaining_separators[separator_index + 1 :]
        if separator == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        # Add separators back to all but the final segment so sentence and
        # paragraph boundaries survive splitting.
        raw_parts = current_text.split(separator)
        parts = [part + separator for part in raw_parts[:-1]]
        if raw_parts[-1]:
            parts.append(raw_parts[-1])

        chunks: list[str] = []
        buffer = ""
        for part in parts:
            if len(part) > self.chunk_size:
                if buffer.strip():
                    chunks.append(buffer)
                    buffer = ""
                chunks.extend(self._split(part, later_separators))
            elif len(buffer) + len(part) <= self.chunk_size:
                buffer += part
            else:
                if buffer.strip():
                    chunks.append(buffer)
                buffer = part

        if buffer.strip():
            chunks.append(buffer)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        safe_chunk_size = max(1, chunk_size)
        strategies = {
            "fixed_size": FixedSizeChunker(
                chunk_size=safe_chunk_size,
                overlap=min(50, safe_chunk_size - 1),
            ),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=safe_chunk_size),
        }

        comparison: dict[str, dict[str, object]] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (sum(len(chunk) for chunk in chunks) / len(chunks)) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
