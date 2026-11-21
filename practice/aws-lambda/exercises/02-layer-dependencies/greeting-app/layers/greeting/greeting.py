"""Shared helpers published in the greeting layer."""
import humanize


def greet(name, count):
    """Return a greeting such as 'Hello, Ada! You have 1,234 new messages.'"""
    noun = "message" if count == 1 else "messages"
    return f"Hello, {name}! You have {humanize.intcomma(count)} new {noun}."
