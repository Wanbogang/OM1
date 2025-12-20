import hashlib
import hmac

from flask import abort, request


def verify_hmac(shared_secret: str, header_name="X-CC-Webhook-Signature"):
    signature = request.headers.get(header_name, "")
    payload = request.get_data()
    expected = hmac.new(shared_secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        abort(400, "Invalid webhook signature")
