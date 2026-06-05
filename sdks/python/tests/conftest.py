import pytest

from nelvra.instruments import openai as openai_instrument
from nelvra.instruments import anthropic as anthropic_instrument


@pytest.fixture(autouse=True)
def reset_instruments():
    """Ensures each test starts with a clean (un-patched) instrument state."""
    openai_instrument._reset_for_testing()
    anthropic_instrument._reset_for_testing()
    yield
    openai_instrument._reset_for_testing()
    anthropic_instrument._reset_for_testing()
