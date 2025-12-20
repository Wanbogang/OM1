from threading import Thread

from flask import Blueprint, jsonify, request

from src.payments.tx_monitor import monitor_tx_background

bp = Blueprint("wallet_order", __name__, url_prefix="/api")


@bp.route("/order_with_wallet", methods=["POST"])
def order_with_wallet():
    data = request.get_json() or {}
    tx_hash = data.get("tx_hash")
    order_id = data.get("order_id")
    if not tx_hash or not order_id:
        return jsonify({"error": "tx_hash and order_id required"}), 400
    # spawn background monitor
    Thread(target=monitor_tx_background, args=(tx_hash, order_id)).start()
    return (
        jsonify({"status": "monitoring", "tx_hash": tx_hash, "order_id": order_id}),
        202,
    )
