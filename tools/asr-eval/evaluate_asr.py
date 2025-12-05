#!/usr/bin/env python3
import argparse
import base64
import csv
import json
import os
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
import pandas as pd
import websocket
from dotenv import load_dotenv
from jiwer import cer, wer

load_dotenv()
API_KEY = os.getenv("OM_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit(
        "ERROR: OM_API_KEY tidak ditemukan. Simpan di .env (tidak di-commit)."
    )
ASR_ENDPOINT = (
    os.getenv("OM1_ASR_ENDPOINT", "https://api.openmind.org/v1/asr") or ""
).strip()
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def transcribe_file(client: httpx.Client, wav_path: str, lang: str) -> str:
    """Kirim audio base64 (WAV 16 kHz mono, <10s) ke endpoint ASR OM1."""
    with open(wav_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    payload = {
        "audio": {"content": b64, "mime_type": "audio/wav"},
        "config": {"language": lang},
    }
    r = client.post(ASR_ENDPOINT, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    text = data.get("text", "") or data.get("transcript", "")
    return text.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--payload-style",
        choices=["v1", "v1-lang", "v2", "raw"],
        default=(os.getenv("ASR_PAYLOAD_STYLE", "v1") or "v1"),
    )
    parser.add_argument("--debug-ws", action="store_true")
    args = parser.parse_args()
    manifest = "tools/asr-eval/manifest.csv"
    out_csv = "tools/asr-eval/out/results.csv"
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    rows = []

    # sinkronkan flag CLI ke env agar fungsi WS bisa membaca
    os.environ["ASR_PAYLOAD_STYLE"] = args.payload_style
    if args.debug_ws:
        os.environ["ASR_DEBUG_WS"] = "1"
    with httpx.Client() as client, open(manifest, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = row["lang"].strip()
            path = os.path.join("tools/asr-eval", row["path"].strip())
            ref = row["reference"].strip()
            if not os.path.isfile(path):
                print(f"[WARN] File tidak ditemukan, skip: {path}")
                continue

            try:
                hyp = transcribe_any(client, path, lang)
                rows.append(
                    {
                        "lang": lang,
                        "path": row["path"].strip(),
                        "reference": ref,
                        "hypothesis": hyp,
                        "wer": wer(ref, hyp),
                        "cer": cer(ref, hyp),
                    }
                )
                time.sleep(0.5)  # throttle ringan
            except httpx.HTTPStatusError as e:
                body = ""
                try:
                    body = e.response.text[:200]
                except Exception:
                    pass
                print(f"[ERROR] HTTP {e.response.status_code} untuk {path}: {body}")
            except Exception as e:
                print(f"[ERROR] {path}: {e}")
    if not rows:
        print("[INFO] Tidak ada hasil. Pastikan file WAV tersedia.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"[OK] Tersimpan: {out_csv}")
    print(df.groupby("lang")[["wer", "cer"]].mean())

    report_md = "tools/asr-eval/out/REPORT.md"
    with open(report_md, "w", encoding="utf-8") as rf:
        rf.write("# ASR Multilingual Mini-Benchmark (OM1)\n\n")
        rf.write("## Rata-rata per bahasa\n\n")
        for lang, g in df.groupby("lang"):
            rf.write(
                f"- **{lang}**: WER={g['wer'].mean():.3f}, CER={g['cer'].mean():.3f}\n"
            )
        rf.write(
            "\n## Catatan\n- Dataset mini (<10 klip/bahasa)\n- Audio WAV 16kHz mono\n- Endpoint: ASR OM1\n"
        )


def _append_api_key(url: str, api_key: str) -> str:
    pr = urlparse(url)
    qs = dict(parse_qsl(pr.query))
    qs["api_key"] = api_key
    new_qs = urlencode(qs)
    return urlunparse((pr.scheme, pr.netloc, pr.path, pr.params, new_qs, pr.fragment))


def _ws_transcribe_variants(ws, b64, lang=None, style="v1", debug=False):
    """
    Try multiple payload variants. 'style': 'v1', 'v1-lang', 'v2', 'raw'.
    """
    # default list; will be narrowed by style
    variants = [
        {"audio": b64, "rate": 16000},  # v1
        {"audio": b64},  # v2
        b64,  # raw
    ]
    if style == "v1-lang" and lang:
        variants = [{"audio": b64, "rate": 16000, "language": lang}]
    elif style == "v1":
        variants = [{"audio": b64, "rate": 16000}]
    elif style == "v2":
        variants = [{"audio": b64}]
    elif style == "raw":
        variants = [b64]
    elif lang:
        variants.insert(0, {"audio": b64, "rate": 16000, "language": lang})

    for payload in variants:
        try:
            if debug:
                print(
                    "[WS->]", payload if isinstance(payload, str) else f"JSON:{payload}"
                )
            ws.send(json.dumps(payload) if not isinstance(payload, str) else payload)
            for _ in range(20):
                msg = ws.recv()
                if debug:
                    if isinstance(msg, (bytes, bytearray)):
                        print("[WS<-] <bytes>")
                    else:
                        m = msg if len(msg) <= 120 else msg[:120] + "..."
                        print("[WS<-]", m)
                try:
                    data = (
                        json.loads(msg)
                        if not isinstance(msg, (bytes, bytearray))
                        else {}
                    )
                except Exception:
                    data = {}
                if isinstance(data, dict):
                    for key in ("asr_reply", "text", "transcript"):
                        if key in data and data.get(key):
                            return str(data.get(key)).strip()
        except Exception:
            continue
    return ""


def _append_api_key(url: str, api_key: str) -> str:
    pr = urlparse(url)
    qs = dict(parse_qsl(pr.query))
    qs["api_key"] = api_key
    new_qs = urlencode(qs)
    return urlunparse((pr.scheme, pr.netloc, pr.path, pr.params, new_qs, pr.fragment))


def transcribe_any(client, wav_path: str, lang: str) -> str:
    if ASR_ENDPOINT.startswith(("ws://", "wss://")):
        with open(wav_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        ws_url = _append_api_key(ASR_ENDPOINT, API_KEY)
        ws = websocket.create_connection(ws_url, timeout=30)
        try:
            # map lang pendek -> locale
            lang_map = {"en": "en-US", "id": "id-ID", "ja": "ja-JP", "zh": "zh-CN"}
            locale = lang_map.get((lang or "").lower())
            text = _ws_transcribe_variants(
                ws,
                b64,
                locale,
                style=os.getenv("ASR_PAYLOAD_STYLE", "v1"),
                debug=os.getenv("ASR_DEBUG_WS") == "1",
            )
            return text
        finally:
            try:
                ws.close()
            except Exception:
                pass
    return transcribe_file(client, wav_path, lang)


def _ws_transcribe_variants(ws, b64, lang=None, style="v1", debug=False):
    """
    Try multiple payload variants. 'style': 'v1', 'v1-lang', 'v2', 'raw'.
    """
    # default list; will be narrowed by style
    variants = [
        {"audio": b64, "rate": 16000},  # v1
        {"audio": b64},  # v2
        b64,  # raw
    ]
    if style == "v1-lang" and lang:
        variants = [{"audio": b64, "rate": 16000, "language": lang}]
    elif style == "v1":
        variants = [{"audio": b64, "rate": 16000}]
    elif style == "v2":
        variants = [{"audio": b64}]
    elif style == "raw":
        variants = [b64]
    elif lang:
        variants.insert(0, {"audio": b64, "rate": 16000, "language": lang})

    for payload in variants:
        try:
            if debug:
                print(
                    "[WS->]", payload if isinstance(payload, str) else f"JSON:{payload}"
                )
            ws.send(json.dumps(payload) if not isinstance(payload, str) else payload)
            for _ in range(20):
                msg = ws.recv()
                if debug:
                    if isinstance(msg, (bytes, bytearray)):
                        print("[WS<-] <bytes>")
                    else:
                        m = msg if len(msg) <= 120 else msg[:120] + "..."
                        print("[WS<-]", m)
                try:
                    data = (
                        json.loads(msg)
                        if not isinstance(msg, (bytes, bytearray))
                        else {}
                    )
                except Exception:
                    data = {}
                if isinstance(data, dict):
                    for key in ("asr_reply", "text", "transcript"):
                        if key in data and data.get(key):
                            return str(data.get(key)).strip()
        except Exception:
            continue
    return ""


if __name__ == "__main__":
    main()
