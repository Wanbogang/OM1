#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Tuple


def fmt_srt_time(t: float) -> str:
    if t is None:
        t = 0.0
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def fmt_vtt_time(t: float) -> str:
    if t is None:
        t = 0.0
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


def write_txt(path: Path, text: str):
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_json(path: Path, segments):
    obj = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_srt(path: Path, segments):
    lines = []
    for i, s in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{fmt_srt_time(s.start)} --> {fmt_srt_time(s.end)}")
        lines.append(s.text.strip())
        lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def write_vtt(path: Path, segments):
    out = ["WEBVTT", ""]
    for s in segments:
        out.append(f"{fmt_vtt_time(s.start)} --> {fmt_vtt_time(s.end)}")
        out.append(s.text.strip())
        out.append("")
    path.write_text("\n".join(out).strip() + "\n", encoding="utf-8")


def discover_inputs(inp: Path) -> List[Path]:
    exts = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus"}
    if inp.is_dir():
        files = [p for p in inp.rglob("*") if p.suffix.lower() in exts]
        return sorted(files)
    elif inp.is_file():
        return [inp]
    else:
        print(f"[ERR] Input not found: {inp}", file=sys.stderr)
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Batch ASR with faster-whisper")
    parser.add_argument("--input", "-i", required=True, help="Audio file or directory")
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="Where to write outputs (default: alongside inputs)",
    )
    parser.add_argument(
        "--model",
        default="small",
        help="faster-whisper model (tiny|base|small|medium|large-v2, etc.)",
    )
    parser.add_argument(
        "--device", default="cpu", choices=["cpu", "cuda"], help="Device"
    )
    parser.add_argument(
        "--compute-type",
        dest="compute_type",
        default=None,
        help="e.g., int8 (CPU), float16 (CUDA); auto if omitted",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Force language (e.g., en, id). If omitted, auto-detect",
    )
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument(
        "--vad", action="store_true", help="Enable VAD (voice activity detection)"
    )
    parser.add_argument(
        "--formats",
        default="txt,srt,vtt,json",
        help="Comma-separated: txt,srt,vtt,json",
    )
    args = parser.parse_args()

    # Correct imports
    try:
        from faster_whisper import WhisperModel

        try:
            from faster_whisper.vad import VadOptions  # <- path yang benar
        except Exception:
            VadOptions = None
    except Exception:
        print(
            "[ERR] faster-whisper not installed. Run: pip install faster-whisper soundfile",
            file=sys.stderr,
        )
        raise

    # Default compute_type
    if args.compute_type is None:
        args.compute_type = "float16" if args.device == "cuda" else "int8"

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)

    inp = Path(args.input)
    out_root = Path(args.output_dir) if args.output_dir else None
    outputs = set(x.strip().lower() for x in args.formats.split(",") if x.strip())

    files = discover_inputs(inp)
    if not files:
        print("[WARN] No audio files found.")
        return

    rows_for_csv: List[Tuple[str, str]] = []
    for idx, audio in enumerate(files, 1):
        rel = audio.name if inp.is_file() else str(audio.relative_to(inp))
        print(f"[{idx}/{len(files)}] Transcribing: {rel}")

        # VAD options (only if available)
        vad_params = None
        vad_filter = False
        if args.vad and VadOptions is not None:
            vad_params = VadOptions(min_silence_duration_ms=250, speech_pad_ms=120)
            vad_filter = True
        elif args.vad and VadOptions is None:
            print(
                "[WARN] VAD requested but VadOptions not available in this faster-whisper version; continuing without VAD.",
                file=sys.stderr,
            )

        # Transcribe
        segments, info = model.transcribe(
            str(audio),
            beam_size=args.beam_size,
            language=args.language,
            vad_filter=vad_filter,
            vad_parameters=vad_params,
        )
        segs = list(segments)
        transcript_text = " ".join(s.text.strip() for s in segs).strip()

        # Output paths
        base_out_dir = out_root or audio.parent
        base_out_dir.mkdir(parents=True, exist_ok=True)
        stem = audio.stem

        if "txt" in outputs:
            write_txt(base_out_dir / f"{stem}.txt", transcript_text)
        if "json" in outputs:
            write_json(base_out_dir / f"{stem}.json", segs)
        if "srt" in outputs:
            write_srt(base_out_dir / f"{stem}.srt", segs)
        if "vtt" in outputs:
            write_vtt(base_out_dir / f"{stem}.vtt", segs)

        rows_for_csv.append((str(audio), transcript_text))

    if not inp.is_file():  # batch mode → write summary CSV
        csv_path = (out_root or inp) / "asr_results.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["file", "transcript"])
            w.writerows(rows_for_csv)
        print(f"[OK] CSV summary: {csv_path}")

    print("[DONE]")


if __name__ == "__main__":
    main()
