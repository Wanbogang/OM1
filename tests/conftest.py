# tests/conftest.py
import sys
from types import SimpleNamespace

# buat modul 'cdp' palsu jika tidak ada
if "cdp" not in sys.modules:
    class DummyWallet:
        def __init__(self, *a, **k): pass
        @staticmethod
        def fetch(_id):
            return SimpleNamespace(balance=lambda asset: "0.12345")
    class DummyCdp:
        @staticmethod
        def configure(a,b): pass

    fake = SimpleNamespace(Cdp=DummyCdp, Wallet=DummyWallet)
    sys.modules["cdp"] = fake
