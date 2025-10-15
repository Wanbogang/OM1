#!/usr/bin/env bash
set -e
export MISTRAL_API_KEY="${MISTRAL_API_KEY:-}"
export MISTRAL_BASE_URL="${MISTRAL_BASE_URL:-https://api.mistral.ai}"
python3 - <<'PY'
from src.llm.plugins.mistral_our_impl.adapter import MistralAdapter
m = MistralAdapter({})
print("health:", m.health_check())
try:
    out = m.generate("Hello from our minimal demo", max_tokens=50)
    print("=> RESPONSE:", out)
except Exception as e:
    print("ERROR:", type(e).__name__, str(e))
PY
