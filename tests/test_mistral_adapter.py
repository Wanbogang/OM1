from src.llm.plugins.mistral_our_impl.adapter import MistralAdapter
import pytest

def test_health_check_bool():
    a = MistralAdapter({})
    assert isinstance(a.health_check(), bool)

def test_generate_empty_raises():
    a = MistralAdapter({})
    with pytest.raises(ValueError):
        a.generate("")
