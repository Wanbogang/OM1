from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/api/order_status_callback", methods=["POST"])
def order_status_callback():
    data = request.get_json() or {}
    print("ORDER UPDATE:", data)
    # TODO: simpan ke DB atau emit ke assistant via webhook/socket
    return jsonify({"ok": True})
