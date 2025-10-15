# Minimal independent Mistral adapter — keep simple & auditable
import os, time, json
from typing import Dict, Any, Optional
import requests

DEFAULT_BASE = "https://api.mistral.ai"
TIMEOUT = 10
RETRIES = 2

class AdapterError(Exception):
    pass

class MistralAdapter:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None):
        cfg = cfg or {}
        self.api_key = cfg.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
        self.base_url = cfg.get("MISTRAL_BASE_URL") or os.getenv("MISTRAL_BASE_URL") or DEFAULT_BASE
        self.timeout = int(cfg.get("timeout", TIMEOUT))
        self.retries = int(cfg.get("retries", RETRIES))

    def health_check(self) -> bool:
        if not (self.api_key or self.base_url):
            return False
        try:
            r = requests.head(self.base_url.rstrip("/") + "/", timeout=3)
            return r.status_code < 500
        except Exception:
            return bool(self.api_key)

    def _call(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        headers = {"Content-Type":"application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        attempt = 0
        backoff = 0.5
        while attempt <= self.retries:
            attempt += 1
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                if r.status_code >= 500 and attempt <= self.retries:
                    time.sleep(backoff); backoff *= 1.5; continue
                try:
                    return r.json()
                except ValueError:
                    raise AdapterError(f"Bad JSON (status {r.status_code})")
            except requests.Timeout:
                if attempt <= self.retries:
                    time.sleep(backoff); backoff *= 1.5; continue
                raise AdapterError("Timeout")
            except requests.RequestException as e:
                if attempt <= self.retries:
                    time.sleep(backoff); backoff *= 1.5; continue
                raise AdapterError("Network error") from e
        raise AdapterError("Failed after retries")

    def _normalize(self, data: Any) -> str:
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            outs = data.get("outputs")
            if isinstance(outs, list) and outs:
                parts = []
                for it in outs:
                    if isinstance(it, dict) and "content" in it:
                        parts.append(it["content"] if isinstance(it["content"], str) else json.dumps(it["content"], ensure_ascii=False))
                    else:
                        parts.append(str(it))
                return "\n".join(parts)
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                c0 = choices[0]
                if isinstance(c0, dict):
                    if "text" in c0: return str(c0["text"])
                    msg = c0.get("message") or {}
                    if isinstance(msg, dict) and "content" in msg: return str(msg["content"])
                return str(c0)
            for k in ("text","result","content"):
                if k in data and isinstance(data[k], str):
                    return data[k]
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return str(data)

    def generate(self, prompt: str, max_tokens: int = 512, model: str = "mistral-large", **opts) -> str:
        if not prompt:
            raise ValueError("prompt wajib")
        payload = {"model": model, "input": prompt, "max_tokens": int(max_tokens)}
        payload.update(opts or {})
        path = opts.get("_path","/v1/generate").lstrip("/")
        resp = self._call(path, payload)
        return self._normalize(resp)
