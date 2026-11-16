"""End-to-end: pick topic → script → TTS → video → export → optional YouTube."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import history
from .exporter import export_package
from .script_generator import generate_script
from .topics import TOPIC_BANK, pick_topic
from .tts import synthesize_voice
from .video_builder import build_video, slugify


def _choose_topic(cfg: dict[str, Any], topic_id: str | None) -> Any:
    if topic_id:
        return pick_topic(topic_id)
    recent = history.recently_used_topic_ids(cfg, limit=max(3, len(TOPIC_BANK) // 3))
    fresh = [t for t in TOPIC_BANK if t.id not in recent] or list(TOPIC_BANK)
    return random.choice(fresh)


def run_pipeline(
    cfg: dict[str, Any],
    *,
    topic_id: str | None = None,
    upload: bool | None = None,
    dry_run_script_only: bool = False,
) -> dict[str, Any]:
    topic = _choose_topic(cfg, topic_id)
    script = generate_script(topic, cfg)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = f"{stamp}_{slugify(topic.id)}"
    out_root = Path(cfg["_root"]) / "output" / slug
    out_root.mkdir(parents=True, exist_ok=True)

    (out_root / "script.json").write_text(
        json.dumps(
            {
                "topic_id": script.topic_id,
                "title": script.title,
                "hook": script.hook,
                "narration": script.full_narration,
                "description": script.description,
                "hashtags": script.hashtags,
                "caption_lines": script.caption_lines,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_root / "narration.txt").write_text(script.full_narration + "\n", encoding="utf-8")

    result: dict[str, Any] = {
        "slug": slug,
        "topic_id": topic.id,
        "title": script.title,
        "output_dir": str(out_root),
        "script_path": str(out_root / "script.json"),
    }

    if dry_run_script_only:
        return result

    audio_path = synthesize_voice(script.full_narration, out_root / "voice.mp3", cfg)
    video_path = build_video(script, audio_path, out_root / f"{slug}.mp4", cfg)
    package_dir = export_package(video_path, script, cfg, slug)

    result.update(
        {
            "audio_path": str(audio_path),
            "video_path": str(video_path),
            "package_dir": str(package_dir),
        }
    )

    should_upload = upload if upload is not None else bool((cfg.get("youtube") or {}).get("enabled"))
    if should_upload:
        from .youtube_uploader import save_upload_receipt, upload_short

        yt = upload_short(video_path, script, cfg)
        receipt = out_root / "youtube_upload.json"
        save_upload_receipt(yt, receipt)
        result["youtube"] = yt
        result["youtube_receipt"] = str(receipt)

    history.record(
        cfg,
        {
            "slug": slug,
            "topic_id": topic.id,
            "title": script.title,
            "video_path": result.get("video_path"),
            "youtube": result.get("youtube"),
        },
    )
    (out_root / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_batch(cfg: dict[str, Any], count: int, upload: bool | None = None) -> list[dict[str, Any]]:
    results = []
    used: set[str] = set()
    for _ in range(max(1, count)):
        # Avoid duplicates inside one batch when possible
        recent = history.recently_used_topic_ids(cfg) | used
        choices = [t for t in TOPIC_BANK if t.id not in recent] or list(TOPIC_BANK)
        topic = random.choice(choices)
        used.add(topic.id)
        results.append(run_pipeline(cfg, topic_id=topic.id, upload=upload))
    return results