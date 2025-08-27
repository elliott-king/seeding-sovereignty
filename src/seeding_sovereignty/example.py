"""Example module with type hints."""

from typing import List, Optional


def greet(name: str) -> str:
    """Return a greeting message.

    Args:
        name: The name to greet.

    Returns:
        A greeting message.
    """
    return f"Hello, {name}!"


def process_numbers(numbers: List[int], threshold: Optional[int] = None) -> List[int]:
    """Process a list of numbers.

    Args:
        numbers: List of integers to process.
        threshold: Optional threshold value.

    Returns:
        List of processed numbers.
    """
    if threshold is None:
        return [n * 2 for n in numbers]
    return [n for n in numbers if n > threshold]
