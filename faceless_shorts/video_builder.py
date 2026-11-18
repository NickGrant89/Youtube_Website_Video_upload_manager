"""Assemble vertical Shorts with ffmpeg + Pillow captions."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .script_generator import ScriptPackage


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(cmd)
            + "\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )


def _ffprobe_duration(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def _find_font(cfg: dict[str, Any]) -> str:
    root = Path(cfg["_root"])
    custom = list((root / "assets" / "fonts").glob("*.ttf")) + list(
        (root / "assets" / "fonts").glob("*.otf")
    )
    if custom:
        return str(custom[0])
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ):
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("No font found. Add a .ttf under assets/fonts/")


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _make_gradient_frame(
    width: int, height: int, colors: list[str], path: Path
) -> None:
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    c0 = _hex_to_rgb(colors[0])
    c1 = _hex_to_rgb(colors[min(1, len(colors) - 1)])
    c2 = _hex_to_rgb(colors[min(2, len(colors) - 1)])
    for y in range(height):
        t = y / max(height - 1, 1)
        if t < 0.5:
            u = t / 0.5
            r = int(c0[0] + (c1[0] - c0[0]) * u)
            g = int(c0[1] + (c1[1] - c0[1]) * u)
            b = int(c0[2] + (c1[2] - c0[2]) * u)
        else:
            u = (t - 0.5) / 0.5
            r = int(c1[0] + (c2[0] - c1[0]) * u)
            g = int(c1[1] + (c2[1] - c1[1]) * u)
            b = int(c1[2] + (c2[2] - c1[2]) * u)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    # subtle vignette bars for "faceless short" look
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, width, int(height * 0.12)], fill=(0, 0, 0, 90))
    od.rectangle([0, int(height * 0.78), width, height], fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(path, format="PNG")


def _pick_broll(cfg: dict[str, Any]) -> Path | None:
    root = Path(cfg["_root"])
    folder = root / "assets" / "broll"
    if not folder.exists():
        return None
    patterns = (cfg.get("compliance") or {}).get("disallow_filename_patterns") or []
    candidates: list[Path] = []
    for pattern in ("*.mp4", "*.mov", "*.webm", "*.mkv"):
        candidates.extend(folder.glob(pattern))
    safe: list[Path] = []
    for path in candidates:
        name = path.name.lower()
        if any(bad.lower() in name for bad in patterns):
            continue
        safe.append(path)
    if not safe:
        return None
    safe.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return safe[0]


def _draw_text_with_stroke(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    stroke: str,
    stroke_width: int,
) -> None:
    x, y = xy
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=stroke)
    draw.text((x, y), text, font=font, fill=fill)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if font.getbbox(trial)[2] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _render_caption_pngs(
    script: ScriptPackage,
    duration: float,
    cfg: dict[str, Any],
    out_dir: Path,
) -> list[tuple[Path, float, float]]:
    video_cfg = cfg.get("video") or {}
    width = int(video_cfg.get("width", 1080))
    height = int(video_cfg.get("height", 1920))
    font_path = _find_font(cfg)
    caption_font = ImageFont.truetype(font_path, int(video_cfg.get("font_size", 72)))
    brand_font = ImageFont.truetype(font_path, int(video_cfg.get("title_font_size", 56)))
    fill = video_cfg.get("caption_color", "white")
    stroke = video_cfg.get("caption_stroke", "black")
    stroke_w = int(video_cfg.get("caption_stroke_width", 4))
    brand = cfg.get("brand_name") or cfg.get("niche") or "Shorts"

    lines = script.caption_lines or [script.full_narration]
    # Keep captions readable: merge tiny leftovers
    if len(lines) > 18:
        merged: list[str] = []
        buf = []
        for line in lines:
            buf.append(line)
            if len(" ".join(buf).split()) >= 6:
                merged.append(" ".join(buf))
                buf = []
        if buf:
            merged.append(" ".join(buf))
        lines = merged

    slice_dur = duration / max(len(lines), 1)
    frames: list[tuple[Path, float, float]] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for idx, line in enumerate(lines):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # brand watermark
        _draw_text_with_stroke(
            draw,
            (48, 80),
            str(brand).upper(),
            brand_font,
            fill="#f5f5f5",
            stroke="#000000",
            stroke_width=3,
        )
        wrapped = _wrap_text(line.upper(), caption_font, width - 120)
        total_h = sum(caption_font.getbbox(w)[3] + 12 for w in wrapped)
        y = int(height * 0.55) - total_h // 2
        for wline in wrapped:
            bbox = caption_font.getbbox(wline)
            tw = bbox[2] - bbox[0]
            x = (width - tw) // 2
            _draw_text_with_stroke(
                draw,
                (x, y),
                wline,
                caption_font,
                fill=fill,
                stroke=stroke,
                stroke_width=stroke_w,
            )
            y += bbox[3] - bbox[1] + 12

        path = out_dir / f"cap_{idx:03d}.png"
        img.save(path)
        start = idx * slice_dur
        end = duration if idx == len(lines) - 1 else (idx + 1) * slice_dur
        frames.append((path, start, end))
    return frames


def _build_background_video(
    cfg: dict[str, Any],
    duration: float,
    work: Path,
) -> Path:
    video_cfg = cfg.get("video") or {}
    width = int(video_cfg.get("width", 1080))
    height = int(video_cfg.get("height", 1920))
    fps = int(video_cfg.get("fps", 30))
    out = work / "background.mp4"
    broll = None
    if video_cfg.get("prefer_broll", True):
        broll = _pick_broll(cfg)

    if broll is not None:
        # Scale/crop to 9:16, loop if shorter than narration
        _run(
            [
                "ffmpeg",
                "-y",
                "-stream_loop",
                "-1",
                "-i",
                str(broll),
                "-t",
                f"{duration:.3f}",
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps}",
                "-an",
                "-pix_fmt",
                "yuv420p",
                str(out),
            ]
        )
        return out

    colors = video_cfg.get("gradient_colors") or ["#0a1628", "#1a3a5c", "#c45c26"]
    still = work / "gradient.png"
    _make_gradient_frame(width, height, colors, still)
    # Slow zoom ken-burns style via zoompan
    frames = max(int(duration * fps), 1)
    _run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(still),
            "-vf",
            f"zoompan=z='min(zoom+0.0004,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}",
            "-t",
            f"{duration:.3f}",
            "-an",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ]
    )
    return out


def build_video(
    script: ScriptPackage,
    audio_path: Path,
    output_path: Path,
    cfg: dict[str, Any],
) -> Path:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required but was not found on PATH")

    video_cfg = cfg.get("video") or {}
    max_seconds = float(video_cfg.get("max_seconds", 45))
    audio_dur = _ffprobe_duration(audio_path)
    duration = min(audio_dur + 0.35, max_seconds)
    fps = int(video_cfg.get("fps", 30))
    width = int(video_cfg.get("width", 1080))
    height = int(video_cfg.get("height", 1920))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="faceless_short_") as tmp:
        work = Path(tmp)
        bg = _build_background_video(cfg, duration, work)
        caps = _render_caption_pngs(script, duration, cfg, work / "caps")

        # Build ffmpeg overlay filter graph
        inputs = ["-i", str(bg), "-i", str(audio_path)]
        filter_parts: list[str] = []
        last = "[0:v]"
        for i, (cap_path, start, end) in enumerate(caps):
            inputs.extend(["-i", str(cap_path)])
            inp_idx = i + 2
            out_label = f"[v{i}]"
            enable = f"between(t\\,{start:.3f}\\,{end:.3f})"
            filter_parts.append(
                f"{last}[{inp_idx}:v]overlay=0:0:enable='{enable}'{out_label}"
            )
            last = out_label

        if not filter_parts:
            filter_complex = f"[0:v]scale={width}:{height}[vout]"
            last = "[vout]"
        else:
            filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            last,
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(fps),
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        _run(cmd)

    if not output_path.exists():
        raise RuntimeError("Video render failed — output missing")
    return output_path


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:60] or "short"