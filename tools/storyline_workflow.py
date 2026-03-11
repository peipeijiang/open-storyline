#!/usr/bin/env python3
"""
Run FireRed-OpenStoryline workflow by API:
1) create session
2) optionally upload media
3) run one or more chat turns
4) collect tool summaries and best-effort rendered video paths
"""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import error, parse, request

# Avoid proxy interception for local service calls (common in corp/dev environments).
for _k in (
    "http_proxy",
    "https_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "all_proxy",
    "ALL_PROXY",
    "ws_proxy",
    "wss_proxy",
    "WS_PROXY",
    "WSS_PROXY",
):
    os.environ.pop(_k, None)
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
request.install_opener(request.build_opener(request.ProxyHandler({})))


def _json_request(url: str, method: str = "GET", payload: Optional[dict] = None) -> dict:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {msg}") from e


def _multipart_post(url: str, files: List[Path], field_name: str = "files") -> dict:
    boundary = f"----openstoryline-{uuid.uuid4().hex}"
    data = bytearray()

    for p in files:
        ctype = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        data.extend(f"--{boundary}\r\n".encode())
        data.extend(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{p.name}"\r\n'.encode()
        )
        data.extend(f"Content-Type: {ctype}\r\n\r\n".encode())
        data.extend(p.read_bytes())
        data.extend(b"\r\n")

    data.extend(f"--{boundary}--\r\n".encode())

    req = request.Request(
        url=url,
        method="POST",
        data=bytes(data),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {msg}") from e


@dataclass
class TurnResult:
    prompt: str
    assistant_text: str = ""
    tool_summaries: List[Dict[str, Any]] = field(default_factory=list)
    render_paths: List[str] = field(default_factory=list)


def _extract_preview_paths(summary: Any) -> List[str]:
    if isinstance(summary, dict):
        v = summary.get("preview_urls")
        if isinstance(v, list):
            return [str(x) for x in v if isinstance(x, str)]
    return []


def _infer_from_instruction(instruction: str) -> Dict[str, str]:
    text = (instruction or "").strip()
    low = text.lower()

    narration_lang = ""
    subtitle_lang = ""
    voice_gender = ""
    subtitle_mode = "optional"

    if ("english" in low) or ("英文" in text):
        narration_lang = "English"
        subtitle_lang = "English"
    elif ("中文" in text) or ("chinese" in low) or ("mandarin" in low):
        narration_lang = "Chinese"
        subtitle_lang = "Chinese"

    if ("female" in low) or ("女声" in text) or ("女生" in text):
        voice_gender = "female"
    elif ("male" in low) or ("男声" in text) or ("男生" in text):
        voice_gender = "male"

    if ("no subtitle" in low) or ("without subtitle" in low) or ("不要字幕" in text) or ("关闭字幕" in text):
        subtitle_mode = "off"
    elif ("subtitle optional" in low) or ("optional subtitles" in low) or ("字幕可选" in text):
        subtitle_mode = "optional"
    elif ("subtitle" in low) or ("subtitles" in low) or ("字幕" in text):
        subtitle_mode = "on"

    return {
        "narration_lang": narration_lang,
        "subtitle_lang": subtitle_lang,
        "voice_gender": voice_gender,
        "subtitle_mode": subtitle_mode,
    }


def _build_prompts_from_instruction(
    instruction: str,
    lang: str = "zh",
    force_two_stage: bool = True,
) -> List[str]:
    pref = _infer_from_instruction(instruction)
    narr_lang = pref["narration_lang"] or ("English" if lang == "en" else "Chinese")
    sub_lang = pref["subtitle_lang"] or narr_lang
    voice_gender = pref["voice_gender"] or "natural"
    subtitle_mode = pref["subtitle_mode"]

    subtitle_clause = {
        "on": f"Subtitles must be enabled in {sub_lang}.",
        "off": "Do not add subtitles.",
        "optional": f"Subtitles are optional; add {sub_lang} subtitles only when they improve clarity.",
    }[subtitle_mode]

    stage1 = (
        "First complete media understanding, clip filtering, and grouping with a concise narrative plan. "
        "Do not render yet."
    )
    stage2 = (
        "Execute to final export now without asking for confirmation. "
        f"Generate {narr_lang} script and {voice_gender} {narr_lang} voiceover. "
        f"{subtitle_clause} "
        "Select suitable BGM with beat alignment, build timeline, render, and export."
    )

    if force_two_stage:
        return [stage1, f"{instruction.strip()}\n\n{stage2}".strip()]

    one_shot = (
        f"{instruction.strip()}\n\n"
        "Directly execute the full pipeline to final export without confirmation. "
        f"Use {narr_lang} script and {voice_gender} {narr_lang} voiceover. {subtitle_clause}"
    ).strip()
    return [one_shot]


async def _run_turns_ws(
    ws_url: str,
    prompts: List[str],
    attachment_ids: Optional[List[str]] = None,
    lang: str = "zh",
    llm_model: Optional[str] = None,
    vlm_model: Optional[str] = None,
) -> List[TurnResult]:
    try:
        import websockets
    except Exception as e:
        raise RuntimeError(
            "Missing dependency 'websockets'. Install it in your runtime env, e.g. pip install websockets"
        ) from e

    results: List[TurnResult] = []

    async with websockets.connect(ws_url, max_size=8 * 1024 * 1024) as ws:
        # Consume initial session snapshot.
        first = await ws.recv()
        _ = json.loads(first)

        for i, prompt in enumerate(prompts):
            turn = TurnResult(prompt=prompt)
            payload: Dict[str, Any] = {
                "text": prompt,
                "lang": lang,
            }
            if i == 0 and attachment_ids:
                payload["attachment_ids"] = attachment_ids
            if llm_model:
                payload["llm_model"] = llm_model
            if vlm_model:
                payload["vlm_model"] = vlm_model

            await ws.send(json.dumps({"type": "chat.send", "data": payload}, ensure_ascii=False))

            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                mtype = msg.get("type")
                data = msg.get("data") or {}

                if mtype == "assistant.delta":
                    delta = (data.get("delta") or "")
                    if delta:
                        turn.assistant_text += delta
                    continue

                if mtype == "tool.end":
                    rec = {
                        "tool_call_id": data.get("tool_call_id"),
                        "name": data.get("name"),
                        "is_error": bool(data.get("is_error")),
                        "summary": data.get("summary"),
                    }
                    turn.tool_summaries.append(rec)

                    summary = rec.get("summary")
                    paths = _extract_preview_paths(summary)
                    if rec.get("name") == "render_video" and paths:
                        turn.render_paths.extend(paths)
                    continue

                if mtype == "assistant.end":
                    final_text = (data.get("text") or "").strip()
                    if final_text and not turn.assistant_text.strip():
                        turn.assistant_text = final_text
                    break

                if mtype == "error":
                    err = data.get("message") or "unknown error"
                    raise RuntimeError(f"chat turn failed: {err}")

            results.append(turn)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run FireRed-OpenStoryline workflow via API")
    parser.add_argument("--base-url", default="http://127.0.0.1:7860", help="Web API base url")
    parser.add_argument("--lang", default="zh", choices=["zh", "en"])
    parser.add_argument("--media", nargs="*", default=[], help="Local media files to upload")
    parser.add_argument("--prompt", action="append", default=[], help="One workflow prompt per turn; repeat this flag")
    parser.add_argument("--instruction", default="", help="High-level instruction; auto-build prompts when --prompt is not provided")
    parser.add_argument("--one-shot", action="store_true", help="Use one-shot mode when auto-building prompts from --instruction")
    parser.add_argument("--llm-model", default="", help="Optional llm model key")
    parser.add_argument("--vlm-model", default="", help="Optional vlm model key")
    parser.add_argument("--output-json", default="", help="Optional path to save run result JSON")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    prompts = list(args.prompt or [])
    if not prompts:
        if not (args.instruction or "").strip():
            raise RuntimeError("Provide at least one --prompt, or provide --instruction for auto prompt building")
        prompts = _build_prompts_from_instruction(
            instruction=args.instruction,
            lang=args.lang,
            force_two_stage=(not args.one_shot),
        )

    # 1) create session
    session = _json_request(f"{base_url}/api/sessions", method="POST")
    sid = session.get("session_id")
    if not sid:
        raise RuntimeError("create session failed: missing session_id")

    # 2) upload media
    attachment_ids: List[str] = []
    media_files: List[Path] = []
    for m in args.media:
        p = Path(m).expanduser().resolve()
        if not p.exists() or not p.is_file():
            raise RuntimeError(f"media file not found: {p}")
        media_files.append(p)

    if media_files:
        up = _multipart_post(f"{base_url}/api/sessions/{sid}/media", media_files)
        for item in up.get("media", []):
            mid = item.get("id")
            if isinstance(mid, str):
                attachment_ids.append(mid)

    # 3) run chat turns
    ws_base = base_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_base}/ws/sessions/{sid}/chat"
    turn_results = asyncio.run(
        _run_turns_ws(
            ws_url=ws_url,
            prompts=prompts,
            attachment_ids=attachment_ids,
            lang=args.lang,
            llm_model=(args.llm_model or None),
            vlm_model=(args.vlm_model or None),
        )
    )

    render_paths: List[str] = []
    for tr in turn_results:
        for p in tr.render_paths:
            if p not in render_paths:
                render_paths.append(p)

    result = {
        "session_id": sid,
        "base_url": base_url,
        "uploaded_media": [str(p) for p in media_files],
        "render_paths": render_paths,
        "turns": [
            {
                "prompt": t.prompt,
                "assistant_text": t.assistant_text,
                "tool_summaries": t.tool_summaries,
                "render_paths": t.render_paths,
            }
            for t in turn_results
        ],
        "effective_prompts": prompts,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.output_json:
        out = Path(args.output_json).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
