from typing import Iterable


class TestUtils:
    """Utility methods for testing purposes."""

    @staticmethod
    def compare_iterables_ignoring_order(result: Iterable, expected: Iterable) -> bool:
        """Compare two iterables are equal ignoring their order."""
        result = list(result)
        expected = list(expected)

        if len(result) == 0 and len(expected) == 0:
            return True

        for r in result:
            try:
                expected.remove(r)
            except ValueError:
                return False

        return len(expected) == 0
