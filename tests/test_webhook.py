import hashlib
import hmac
import importlib

import pytest

# import fungsi verify_hmac dari src/webhook.py
webhook = importlib.import_module("src.webhook")


class DummyRequest:
    def __init__(self, payload, sig_header):
        self._payload = payload
        self.headers = {"X-CC-Webhook-Signature": sig_header}

    def get_data(self):
        return self._payload


def make_sig(secret, payload):
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_verify_hmac_valid(monkeypatch):
    payload = b'{"test":"ok"}'
    secret = "mysecret"
    sig = make_sig(secret, payload)
    dr = DummyRequest(payload, sig)
    monkeypatch.setattr(webhook, "request", dr)
    # should not raise
    webhook.verify_hmac(secret)


def test_verify_hmac_invalid(monkeypatch):
    payload = b'{"test":"ok"}'
    secret = "mysecret"
    sig = "bad_sig"
    dr = DummyRequest(payload, sig)
    monkeypatch.setattr(webhook, "request", dr)
    with pytest.raises(Exception):
        webhook.verify_hmac(secret)
