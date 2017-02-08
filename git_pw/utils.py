"""
Utility functions.
"""


def trim(string, length=70):
    """Trim a string to the given length."""
    return (string[:length - 1] + '...') if len(string) > length else string
