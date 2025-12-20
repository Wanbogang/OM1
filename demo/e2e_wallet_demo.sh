#!/usr/bin/env bash
set -euo pipefail
echo "=== OM1 Emoji Order Assistant — E2E Demo ==="
echo "1) Pastikan MetaMask aktif di browser (testnet/local)."
echo "2) Server akan dijalankan di http://localhost:8080"
echo

# stop existing
pkill -f server.py || true
sleep 1

# start server
nohup python3 server.py > demo/om1-server.log 2>&1 &
sleep 1

echo "Server started. Logs: demo/om1-server.log"
echo
echo "Open the demo page in your browser:"
echo "  http://localhost:8080/"
echo
echo "Steps to demo (manual):"
echo "  1) Connect Wallet"
echo "  2) Click 'Sign & Send Tx (demo)'"
echo "  3) Confirm in wallet"
echo
echo "After finishing, check orders:"
echo "  curl http://localhost:8080/api/orders"
echo
echo "To stop server: pkill -f server.py"
