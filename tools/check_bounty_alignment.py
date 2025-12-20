#!/usr/bin/env python3
# tools/check_bounty_alignment.py
# Simple repo scanner to check alignment with OM1 bounty requirements.

import re
from pathlib import Path

root = Path.cwd()
print("Repo root:", root)
print()


def find_files_with_pattern(pattern, paths):
    hits = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            if re.search(pattern, txt, re.IGNORECASE):
                hits.append(p)
        except Exception:
            continue
    return hits


# collect files
all_files = [
    p
    for p in root.rglob("*")
    if p.is_file() and p.suffix in {".py", ".md", ".yaml", ".yml", ".js", ".json"}
]

print("Files scanned:", len(all_files))
print()

# checks
checks = []

# 1. Payment handlers / Coinbase / wallet
checks.append(
    (
        "Has payment handler file (payment|pay|coinbase)",
        any(
            re.search(r"payment|pay|coinbase", str(p), re.IGNORECASE) for p in all_files
        ),
    )
)
# 2. Wallet-connected endpoints (order_with_wallet / wallet)
checks.append(
    (
        "Has API route for wallet orders (order_with_wallet / wallet)",
        any(
            find_files_with_pattern(r"order_with_wallet|order_with_wallet", [p])
            for p in all_files
        ),
    )
)
# 3. tx monitor (web3, get_transaction_receipt, to_wei)
checks.append(
    (
        "Uses web3 / tx monitor (web3|get_transaction_receipt|to_wei)",
        any(
            find_files_with_pattern(r"web3|get_transaction_receipt|to_wei|toWei", [p])
            for p in all_files
        ),
    )
)
# 4. Webhook verification HMAC
checks.append(
    (
        "Webhook verify HMAC (X-CC-Webhook-Signature or hmac.compare_digest)",
        any(
            find_files_with_pattern(
                r"X-CC-Webhook-Signature|hmac\.compare_digest|verify_hmac", [p]
            )
            for p in all_files
        ),
    )
)
# 5. Smart assistant / Home Assistant demo
checks.append(
    (
        "Home Assistant demo (demo/home_assistant or rest_command)",
        (root / "demo" / "home_assistant").exists()
        or any(
            find_files_with_pattern(r"home_assistant|rest_command", [p])
            for p in all_files
        ),
    )
)
# 6. Frontend wallet connect (ethers, WalletConnect)
checks.append(
    (
        "Frontend wallet connect (ethers|WalletConnect|wallet_connect.js)",
        any(
            find_files_with_pattern(r"ethers|WalletConnect|wallet_connect", [p])
            for p in all_files
        ),
    )
)
# 7. README mentions Coinbase / wallet
checks.append(
    (
        "README mentions Coinbase or wallet",
        any(
            find_files_with_pattern(
                r"coinbase|walletconnect|wallet", [root / "README.md"]
            )
            if (root / "README.md").exists()
            else []
        ),
    )
)
# 8. Flask app present and route registration
checks.append(
    (
        "Flask app/routes present (Flask\\(|app.route)",
        any(
            find_files_with_pattern(r"Flask\(|@app\.route|Blueprint", [p])
            for p in all_files
        ),
    )
)
# 9. Tests or CI presence
checks.append(
    (
        "Has tests or CI (test_*.py or .github/workflows)",
        any(p.name.startswith("test_") for p in all_files)
        or (root / ".github" / "workflows").exists(),
    )
)

# Print results
print("Quick alignment report with OM1 bounty requirements:\n")
for desc, ok in checks:
    status = "OK" if bool(ok) else "MISSING"
    print(f"- {desc:60} : {status}")
print()

# Detailed hints
print("Hints / recommended next steps (automatic):\n")
if not checks[0][1]:
    print(
        "- Tambahkan modul payment handler (src/payments) atau periksa src/payment_handler.py"
    )
if not checks[1][1]:
    print(
        "- Tambah endpoint POST /api/order_with_wallet yang menerima tx_hash + order_id"
    )
if not checks[2][1]:
    print(
        "- Pastikan ada pemantau tx (web3) yang memanggil get_transaction_receipt dan update order status"
    )
if not checks[3][1]:
    print(
        "- Implementasikan verifikasi webhook (HMAC) untuk Coinbase Commerce jika masih pakai payment gateway"
    )
if not checks[4][1]:
    print(
        "- Tambahkan demo Home Assistant (demo/home_assistant/rest_command.yaml + automation_example.yaml)"
    )
if not checks[5][1]:
    print(
        "- Tambahkan frontend wallet connect (src/static/wallet_connect.js) untuk flow connect & sign tx"
    )
if not checks[6][1]:
    print(
        "- Perbarui README.md untuk mendokumentasikan flow wallet-connected vs Coinbase Commerce"
    )
if not checks[7][1]:
    print(
        "- Pastikan ada Flask app dan route terdaftar (app = Flask(...), app.register_blueprint(...))"
    )
if not checks[8][1]:
    print("- Tambah unit tests sederhana dan/atau GitHub Actions untuk CI")

print("\nDetail file hits (contoh):\n")
# show a few example files that matched key terms
for term in [
    "coinbase",
    "wallet",
    "web3",
    "webhook",
    "home_assistant",
    "ethers",
    "WalletConnect",
    "order_with_wallet",
]:
    hits = find_files_with_pattern(term, all_files)
    if hits:
        print(f"Term '{term}' found in {len(hits)} file(s). Example: {hits[0]}")
print("\nDone.")
