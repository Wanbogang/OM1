# tests/_eth_account_stub.py
import sys
from types import SimpleNamespace
if "eth_account" not in sys.modules:
    class DummyAccount:
        @staticmethod
        def recover_message(msg, signature=None):
            return "0x0000000000000000000000000000000000000000"
    fake = SimpleNamespace(messages=SimpleNamespace(encode_defunct=lambda text: text), Account=DummyAccount)
    sys.modules["eth_account"] = fake
