"""Wrapper for fuzzy matching with a fallback implementation."""
try:
    from rapidfuzz import fuzz  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handle missing optional dependency
    import difflib

    class _FallbackFuzz:
        """Minimal replacement for ``rapidfuzz.fuzz``.

        Only implements ``WRatio`` which returns a score in the range 0-100.
        """

        @staticmethod
        def WRatio(a: str, b: str) -> float:
            # difflib.SequenceMatcher returns 0..1; scale to 0..100
            return difflib.SequenceMatcher(None, a, b).ratio() * 100

    fuzz = _FallbackFuzz()

__all__ = ["fuzz"]
