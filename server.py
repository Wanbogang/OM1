import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="OM1 Emoji Order Assistant")

# simple in-memory store for demo
ORDERS = {}
TX_INDEX = []


@app.post("/api/payment/signed")
async def payment_signed(req: Request):
    payload = await req.json()
    tx_hash = payload.get("txHash")
    order_id = payload.get("order_id")
    now = int(time.time())
    rec = {
        "tx_hash": tx_hash,
        "received_at": now,
        "status": "received",
        "order_id": order_id,
    }
    if order_id:
        if order_id not in ORDERS:
            ORDERS[order_id] = {"order_id": order_id, "payments": []}
        ORDERS[order_id]["payments"].append(rec)
    else:
        key = f"tx-{len(TX_INDEX)+1}"
        ORDERS[key] = rec
        TX_INDEX.append(rec)
    return JSONResponse({"status": "ok", "record": rec})


@app.get("/api/orders")
async def list_orders():
    return ORDERS


@app.get("/healthz")
def health():
    return {"status": "ok"}


# serve static files under /static
static_dir = os.path.join(os.path.dirname(__file__), "web-client")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# root: return index.html
@app.get("/")
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
