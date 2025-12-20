import os
import time

import requests
from web3 import Web3

RPC = os.getenv("ETH_RPC", "https://mainnet.infura.io/v3/YOUR_INFURA_KEY")
w3 = Web3(Web3.HTTPProvider(RPC))


def notify_order_update(order_id, status, tx_hash):
    try:
        requests.post(
            "http://localhost:5000/api/order_status_callback",
            json={"order_id": order_id, "status": status, "tx_hash": tx_hash},
            timeout=5,
        )
    except Exception as e:
        print("notify error", e)


def monitor_tx_background(tx_hash, order_id, poll_interval=8, timeout=1800):
    start = time.time()
    while True:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                status = "success" if receipt.status == 1 else "failed"
                notify_order_update(order_id, status, tx_hash)
                return
        except Exception:
            # tx not yet mined -> continue polling
            pass
        if time.time() - start > timeout:
            notify_order_update(order_id, "timeout", tx_hash)
            return
        time.sleep(poll_interval)
