"""Write ready-to-post package for TikTok / Reels / manual upload."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .script_generator import ScriptPackage


def export_package(
    video_path: Path,
    script: ScriptPackage,
    cfg: dict[str, Any],
    slug: str,
) -> Path:
    export_cfg = cfg.get("export") or {}
    root = Path(cfg["_root"])
    folder = root / export_cfg.get("folder", "output/ready_to_post")
    dest_dir = folder / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_video = dest_dir / f"{slug}.mp4"
    shutil.copy2(video_path, dest_video)

    if export_cfg.get("write_caption_txt", True):
        (dest_dir / "caption.txt").write_text(script.full_narration + "\n", encoding="utf-8")

    hashtag_line = " ".join(f"#{h.lstrip('#')}" for h in script.hashtags)
    if export_cfg.get("write_hashtags", True):
        (dest_dir / "hashtags.txt").write_text(hashtag_line + "\n", encoding="utf-8")

    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "topic_id": script.topic_id,
        "title": script.title,
        "hook": script.hook,
        "description": script.description,
        "hashtags": script.hashtags,
        "video": dest_video.name,
        "platforms": {
            "youtube_shorts": "Use: python -m faceless_shorts upload --video ... or enable auto-upload",
            "tiktok": "Upload caption.txt + video manually or via TikTok Content Posting API (app review required)",
            "instagram_reels": "Upload via Meta Graph API with a Business account, or manually",
        },
        "compliance_note": (
            "Use original commentary and your own or licensed b-roll only. "
            "Do not automate mass reuploads of Rockstar trailers/cutscenes."
        ),
    }
    (dest_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Convenience copy at top of ready_to_post
    shutil.copy2(dest_video, folder / f"{slug}.mp4")
    return dest_dir