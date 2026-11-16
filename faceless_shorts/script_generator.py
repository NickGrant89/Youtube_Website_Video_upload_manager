"""Generate short-form scripts from templates or OpenAI."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .topics import Topic


@dataclass
class ScriptPackage:
    topic_id: str
    title: str
    hook: str
    body: str
    full_narration: str
    description: str
    hashtags: list[str]
    caption_lines: list[str]


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_caption_lines(narration: str, max_words: int = 5) -> list[str]:
    words = narration.split()
    lines: list[str] = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words])
        if chunk:
            lines.append(chunk)
    return lines


def generate_template_script(topic: Topic, cfg: dict[str, Any]) -> ScriptPackage:
    script_cfg = cfg.get("script", {})
    niche = cfg.get("niche", "GTA 6")
    cta = script_cfg.get("call_to_action", "Follow for more tips.")
    points = " ".join(f"{i}. {p}" for i, p in enumerate(topic.points, start=1))
    narration = _clean(
        f"{topic.hook} {points} {cta}"
    )
    # Keep under max_words roughly by trimming middle points if needed
    max_words = int(script_cfg.get("max_words", 110))
    words = narration.split()
    if len(words) > max_words:
        narration = " ".join(words[: max_words - 8] + cta.split())

    title = f"{topic.hook.rstrip('.')} | {niche}"
    if len(title) > 90:
        title = title[:87] + "..."

    hashtags = list(dict.fromkeys([*topic.hashtags, *cfg.get("youtube", {}).get("tags", [])]))
    description = (
        f"{topic.angle}\n\n{narration}\n\n"
        + " ".join(f"#{h.lstrip('#')}" for h in hashtags[:12])
    )
    return ScriptPackage(
        topic_id=topic.id,
        title=title,
        hook=topic.hook,
        body=" ".join(topic.points),
        full_narration=narration,
        description=description,
        hashtags=[h.lstrip("#") for h in hashtags],
        caption_lines=_split_caption_lines(narration),
    )


def generate_openai_script(topic: Topic, cfg: dict[str, Any]) -> ScriptPackage:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing. Set it in .env or use script.mode: template")

    script_cfg = cfg.get("script", {})
    niche = cfg.get("niche", "GTA 6")
    prompt = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write faceless YouTube Shorts narration for gaming tips. "
                    "Return strict JSON with keys: title, narration, description. "
                    "Narration must be spoken aloud in under 45 seconds, punchy, no emoji, "
                    "no claims of leaked/unreleased copyrighted footage. Original commentary only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Niche: {niche}\n"
                    f"Hook: {topic.hook}\n"
                    f"Angle: {topic.angle}\n"
                    f"Points: {list(topic.points)}\n"
                    f"Tone: {script_cfg.get('tone', 'urgent')}\n"
                    f"CTA: {script_cfg.get('call_to_action', 'Follow for more.')}\n"
                    f"Max words: {script_cfg.get('max_words', 110)}"
                ),
            },
        ],
        "temperature": 0.8,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(prompt).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="ignore")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc

    content = payload["choices"][0]["message"]["content"]
    data = json.loads(content)
    narration = _clean(data.get("narration") or topic.hook)
    title = _clean(data.get("title") or topic.hook)[:95]
    description = data.get("description") or narration
    hashtags = list(dict.fromkeys([*topic.hashtags, *cfg.get("youtube", {}).get("tags", [])]))
    description = description + "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags[:12])
    return ScriptPackage(
        topic_id=topic.id,
        title=title,
        hook=topic.hook,
        body=" ".join(topic.points),
        full_narration=narration,
        description=description,
        hashtags=[h.lstrip("#") for h in hashtags],
        caption_lines=_split_caption_lines(narration),
    )


def generate_script(topic: Topic, cfg: dict[str, Any]) -> ScriptPackage:
    mode = (cfg.get("script") or {}).get("mode", "template")
    if mode == "openai":
        return generate_openai_script(topic, cfg)
    return generate_template_script(topic, cfg)