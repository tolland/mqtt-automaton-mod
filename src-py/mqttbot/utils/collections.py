


def first_or_default(iterable, default=None):
    """Returns the first element of an iterable or a default value if the iterable is empty.

    Args:
        iterable: An iterable (e.g., list, tuple, set).
        default: The value to return if the iterable is empty. Defaults to None.
    Returns:"""
    for item in iterable:
        return item
    return default
