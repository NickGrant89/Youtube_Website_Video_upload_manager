"""Text-to-speech via edge-tts (free neural voices)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import edge_tts


async def _synthesize(text: str, out_path: Path, voice: str, rate: str, volume: str) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume)
    await communicate.save(str(out_path))


def synthesize_voice(text: str, out_path: Path, cfg: dict[str, Any]) -> Path:
    tts_cfg = cfg.get("tts") or {}
    voice = tts_cfg.get("voice", "en-US-ChristopherNeural")
    rate = tts_cfg.get("rate", "+0%")
    volume = tts_cfg.get("volume", "+0%")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize(text, out_path, voice, rate, volume))
    if not out_path.exists() or out_path.stat().st_size < 100:
        raise RuntimeError(f"TTS failed to write audio: {out_path}")
    return out_path


async def list_voices(locale_prefix: str = "en") -> list[str]:
    voices = await edge_tts.list_voices()
    names = sorted(
        v["ShortName"]
        for v in voices
        if str(v.get("Locale", "")).lower().startswith(locale_prefix.lower())
    )
    return names