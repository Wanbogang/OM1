from typing import Optional, Dict, Any
from .coinbase import CoinbaseProvider
from .metamask import MetaMaskProvider

def create_provider(name: str, opts: Optional[Dict[str, Any]] = None):
    opts = opts or {}
    n = name.lower()
    if n == "coinbase":
        return CoinbaseProvider(wallet_id=opts.get("wallet_id"))
    if n == "metamask":
        return MetaMaskProvider()
    raise ValueError(f"Unknown provider: {name}")
