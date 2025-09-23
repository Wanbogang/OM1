# ASR Multilingual Mini-Benchmark (OM1)

## Cara jalan singkat

python -m venv .venv
source .venv/bin/activate
pip install -r tools/asr-eval/requirements.txt
python tools/asr-eval/evaluate_asr.py

Output:
- `tools/asr-eval/out/results.csv`
- `tools/asr-eval/out/REPORT.md`

## Catatan
- Audio contoh *tidak* di-commit; isi sendiri `tools/asr-eval/<lang>/...`.
- Pastikan `.env` dan `*.wav` di-ignore oleh git.
