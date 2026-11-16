"""CLI entry: python -m faceless_shorts ..."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .config import load_config
from .pipeline import run_batch, run_pipeline
from .topics import list_topics
from .tts import list_voices


@click.group()
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None) -> None:
    """Faceless Shorts Factory — GTA niche automation."""
    ctx.ensure_object(dict)
    ctx.obj["cfg"] = load_config(config_path)


@cli.command("list-topics")
def list_topics_cmd() -> None:
    """Show built-in topic bank."""
    for topic in list_topics():
        click.echo(f"{topic.id:16}  {topic.hook}")


@cli.command("voices")
@click.option("--prefix", default="en", help="Locale prefix filter")
def voices_cmd(prefix: str) -> None:
    """List edge-tts voices."""
    import asyncio

    voices = asyncio.run(list_voices(prefix))
    for name in voices:
        click.echo(name)


@cli.command("make")
@click.option("--topic", "topic_id", default=None, help="Topic id from list-topics")
@click.option("--upload/--no-upload", default=None, help="Force/disable YouTube upload")
@click.option("--script-only", is_flag=True, help="Generate script JSON only")
@click.pass_context
def make_cmd(
    ctx: click.Context,
    topic_id: str | None,
    upload: bool | None,
    script_only: bool,
) -> None:
    """Generate one short (script → voice → video → export)."""
    cfg = ctx.obj["cfg"]
    if (cfg.get("compliance") or {}).get("remind_copyright", True):
        click.echo(
            "Compliance: original commentary only. Put your own/licensed clips in assets/broll/. "
            "Do not mass-repost Rockstar trailers/cutscenes."
        )
    result = run_pipeline(
        cfg,
        topic_id=topic_id,
        upload=upload,
        dry_run_script_only=script_only,
    )
    click.echo(json.dumps(result, indent=2))


@cli.command("batch")
@click.option("--count", default=3, show_default=True, help="How many shorts to generate")
@click.option("--upload/--no-upload", default=None)
@click.pass_context
def batch_cmd(ctx: click.Context, count: int, upload: bool | None) -> None:
    """Generate multiple shorts in one run."""
    results = run_batch(ctx.obj["cfg"], count=count, upload=upload)
    click.echo(json.dumps(results, indent=2))


@cli.command("upload")
@click.option("--video", "video_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--script", "script_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.pass_context
def upload_cmd(ctx: click.Context, video_path: Path, script_path: Path) -> None:
    """Upload an existing rendered short to YouTube."""
    from .script_generator import ScriptPackage
    from .youtube_uploader import save_upload_receipt, upload_short

    cfg = ctx.obj["cfg"]
    cfg.setdefault("youtube", {})["enabled"] = True
    raw = json.loads(script_path.read_text(encoding="utf-8"))
    script = ScriptPackage(
        topic_id=raw.get("topic_id", "manual"),
        title=raw["title"],
        hook=raw.get("hook", raw["title"]),
        body=raw.get("narration", ""),
        full_narration=raw.get("narration") or raw.get("full_narration", ""),
        description=raw.get("description", ""),
        hashtags=list(raw.get("hashtags") or []),
        caption_lines=list(raw.get("caption_lines") or []),
    )
    result = upload_short(video_path, script, cfg)
    receipt = video_path.with_suffix(".youtube.json")
    save_upload_receipt(result, receipt)
    click.echo(json.dumps(result, indent=2))


@cli.command("schedule")
@click.option("--once", is_flag=True, help="Run one batch now and exit")
@click.pass_context
def schedule_cmd(ctx: click.Context, once: bool) -> None:
    """Run daily local batches (generate + optional YouTube).

    TikTok/Instagram auto-post need their own approved apps; this scheduler
    generates ready_to_post packages and can upload to YouTube when configured.
    """
    cfg = ctx.obj["cfg"]
    sched = cfg.get("scheduler") or {}
    count = int(sched.get("posts_per_day", 2))

    def job() -> None:
        click.echo(f"Running scheduled batch of {count}...")
        results = run_batch(cfg, count=count)
        click.echo(json.dumps(results, indent=2))

    if once:
        job()
        return

    try:
        import schedule
        import time
    except ImportError as exc:
        raise click.ClickException("schedule package missing") from exc

    hour = int(sched.get("run_hour_local", 9))
    schedule.every().day.at(f"{hour:02d}:00").do(job)
    click.echo(f"Scheduler armed — daily at {hour:02d}:00 local. Ctrl+C to stop.")
    job()  # also run immediately so first day isn't empty
    while True:
        schedule.run_pending()
        time.sleep(30)


def main() -> None:
    try:
        cli(obj={})
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()