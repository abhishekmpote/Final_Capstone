"""Recursive character-based text chunking with source-preserving overlap."""

import re


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text at the largest available natural boundary and retain overlap."""
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Chunk overlap must be non-negative and smaller than chunk size.")
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    separators = [". ", "? ", "! ", " "]
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        hard_end = min(start + chunk_size, len(cleaned))
        end = (
            hard_end
            if hard_end == len(cleaned)
            else _recursive_split_point(cleaned, start, hard_end, separators)
        )
        if end <= start:
            end = hard_end
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break

        next_start = max(start + 1, end - overlap)
        if overlap:
            previous_space = cleaned.rfind(" ", start, next_start)
            if previous_space >= start:
                next_start = previous_space + 1
            else:
                next_space = cleaned.find(" ", next_start, end)
                next_start = next_space + 1 if next_space >= 0 else end
        start = next_start
    return chunks


def _recursive_split_point(
    text: str, start: int, hard_end: int, separators: list[str]
) -> int:
    """Prefer sentence and word boundaries, falling back through separators."""
    if not separators:
        return hard_end
    separator = separators[0]
    position = text.rfind(separator, start, hard_end)
    if position > start:
        # Keep sentence punctuation; the following space may be trimmed.
        return position + len(separator.rstrip())
    return _recursive_split_point(text, start, hard_end, separators[1:])
