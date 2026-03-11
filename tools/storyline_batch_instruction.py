#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


def run(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def run_out(cmd: List[str]) -> str:
    p = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return p.stdout.strip()


def ffprobe_duration(path: Path) -> float:
    out = run_out([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nk=1:nw=1", str(path)
    ])
    return float(out)


def choose_latest_understand(outputs_dir: Path) -> Path:
    candidates = sorted(outputs_dir.glob("*/understand_clips/*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No understand_clips json found under outputs/*/understand_clips")
    return candidates[0]


def load_understand(understand_json: Path) -> Tuple[str, List[Dict[str, str]]]:
    session_id = understand_json.parts[-3]
    data = json.loads(understand_json.read_text(encoding="utf-8"))
    clip_caps = (data.get("payload") or {}).get("clip_captions") or []
    rows: List[Dict[str, str]] = []
    for c in clip_caps:
        cid = str(c.get("clip_id") or "")
        cap = str(c.get("caption") or "")
        mid = str((c.get("source_ref") or {}).get("media_id") or "")
        if cid and cap:
            rows.append({"clip_id": cid, "caption": cap, "media_id": mid})
    if not rows:
        raise RuntimeError(f"No clip_captions in {understand_json}")
    return session_id, rows


def find_latest_split_dir(cache_root: Path, session_id: str) -> Path:
    base = cache_root / session_id
    cands = sorted(base.glob("split_shots_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        raise FileNotFoundError(f"No split_shots dir under {base}")
    return cands[0]


def build_keywords(instruction: str) -> List[str]:
    low = instruction.lower()
    toks = re.findall(r"[a-zA-Z]{3,}", low)
    extra = [
        "product", "feature", "health", "sleep", "heart", "oxygen",
        "gesture", "control", "waterproof", "fitness", "design", "smart", "ring"
    ]
    out = set(toks + extra)
    return sorted(out)


def score_clip(caption: str, keywords: List[str]) -> int:
    low = caption.lower()
    s = 0
    for kw in keywords:
        if kw in low:
            s += 2
    # bonus for explicit function terms
    for kw in ["sleep", "heart", "oxygen", "gesture", "waterproof", "fitness", "control"]:
        if kw in low:
            s += 3
    return s


def collect_voice_wavs(outputs_dir: Path, min_count: int = 5) -> List[List[Path]]:
    dirs = sorted(outputs_dir.glob("*/generate_voiceover"), key=lambda p: p.stat().st_mtime, reverse=True)
    groups: List[List[Path]] = []
    for d in dirs:
        wavs = sorted(d.glob("voiceover_*.wav"))
        if len(wavs) >= min_count:
            groups.append(wavs)
    if not groups:
        raise RuntimeError("No usable generate_voiceover dirs found")
    return groups


def make_audio_track(wavs: List[Path], out_audio: Path, duration: float) -> None:
    concat_file = out_audio.with_suffix(".concat.txt")
    concat_file.write_text("\n".join([f"file '{w}'" for w in wavs]) + "\n", encoding="utf-8")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-af", "apad=pad_dur=90", "-t", str(duration),
        "-c:a", "aac", "-b:a", "192k", str(out_audio)
    ])


def make_video_track(clip_files: List[Path], out_video: Path, duration: float, seed: int) -> None:
    rnd = random.Random(seed)
    work_dir = out_video.parent
    segs: List[Path] = []
    seg_dur = 7.5
    target_segments = int(duration / seg_dur)
    if target_segments < 1:
        target_segments = 1

    for i in range(target_segments):
        clip = clip_files[(i + seed) % len(clip_files)]
        c_dur = ffprobe_duration(clip)
        if c_dur <= seg_dur + 0.1:
            ss = 0.0
        else:
            ss = rnd.uniform(0, max(0.0, c_dur - seg_dur - 0.05))
        seg = work_dir / f"seg_{i+1:02d}.mp4"
        run([
            "ffmpeg", "-y", "-ss", f"{ss:.3f}", "-i", str(clip), "-t", str(seg_dur), "-an",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(seg)
        ])
        segs.append(seg)

    concat_file = work_dir / "video.concat.txt"
    concat_file.write_text("\n".join([f"file '{s}'" for s in segs]) + "\n", encoding="utf-8")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-t", str(duration), str(out_video)
    ])


def mux_av(video: Path, audio: Path, out_path: Path, duration: float) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-t", str(duration), str(out_path)
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description="Instruction-driven batch production for OpenStoryline")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--instruction", required=True)
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--duration", type=float, default=45.0)
    ap.add_argument("--session-id", default="", help="Optional fixed session id to read understand/split artifacts")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    outputs_dir = root / "outputs"
    cache_root = root / ".storyline" / ".server_cache"

    if args.session_id:
        # pick newest understand file from that session
        cands = sorted((outputs_dir / args.session_id / "understand_clips").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not cands:
            raise FileNotFoundError(f"No understand_clips json under outputs/{args.session_id}/understand_clips")
        understand_json = cands[0]
    else:
        understand_json = choose_latest_understand(outputs_dir)

    session_id, rows = load_understand(understand_json)
    split_dir = find_latest_split_dir(cache_root, session_id)
    keywords = build_keywords(args.instruction)

    scored: List[Tuple[int, Path]] = []
    for r in rows:
        clip_path = split_dir / f"{r['clip_id']}.mp4"
        if not clip_path.exists():
            continue
        s = score_clip(r["caption"], keywords)
        scored.append((s, clip_path))

    if not scored:
        raise RuntimeError("No clip files matched between understand_clips and split_shots")

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [p for _, p in scored[: max(20, min(60, len(scored)))]]

    voice_groups = collect_voice_wavs(outputs_dir)

    out_dir = Path(args.out_dir).resolve() if args.out_dir else (outputs_dir / f"batch_instruction_{int(random.random()*1e9):09d}")
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_root = out_dir / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)

    rnd = random.Random(args.seed)
    manifest = {
        "instruction": args.instruction,
        "count": args.count,
        "duration": args.duration,
        "session_id": session_id,
        "split_dir": str(split_dir),
        "files": []
    }

    for i in range(1, args.count + 1):
        work = temp_root / f"v{i:02d}"
        work.mkdir(parents=True, exist_ok=True)

        # rotate clip subset for diversity
        shift = (i * 3) % len(top)
        clip_pool = top[shift:] + top[:shift]

        v_out = work / "video45.mp4"
        a_out = work / "voice45.m4a"

        make_video_track(clip_pool, v_out, args.duration, seed=args.seed + i)

        voice_wavs = voice_groups[(i - 1) % len(voice_groups)]
        # sample up to 12 segments for diversity
        if len(voice_wavs) > 12:
            chosen = sorted(rnd.sample(voice_wavs, 12))
        else:
            chosen = voice_wavs
        make_audio_track(chosen, a_out, args.duration)

        final = out_dir / f"instruction_batch_en_female_voiceonly_{i:02d}.mp4"
        mux_av(v_out, a_out, final, args.duration)
        d = ffprobe_duration(final)

        manifest["files"].append({
            "index": i,
            "path": str(final),
            "duration": d,
            "voice_source_count": len(chosen)
        })

    man = out_dir / "manifest.json"
    man.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"out_dir": str(out_dir), "manifest": str(man), "count": len(manifest["files"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
