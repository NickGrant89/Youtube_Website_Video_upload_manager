# Faceless Shorts Factory (GTA niche)

Automate **faceless vertical shorts**: topic → script → AI voice → captioned 9:16 video → export package → optional **YouTube Shorts** upload.

This is built for the “make money around GTA 6 launch” workflow: original tip/news-style commentary, not stolen trailers.

## What it automates

| Step | Automated? | Notes |
|------|------------|--------|
| Topic + hook selection | Yes | Built-in GTA 6 topic bank, rotates history |
| Script writing | Yes | Templates by default; optional OpenAI |
| Voiceover | Yes | Free neural TTS (`edge-tts`) |
| Captioned 9:16 video | Yes | ffmpeg + Pillow; gradient or your b-roll |
| Export for TikTok/Reels | Yes | `output/ready_to_post/<slug>/` |
| YouTube Shorts upload | Yes (optional) | Official YouTube Data API + OAuth |
| TikTok / Instagram post | Export only | Needs their approved APIs + business apps |

**Hard limits (by design):** no scraping Rockstar trailers, no unofficial “auto-post everywhere” bots that break platform rules, no cracked game footage pipeline. Put **your own gameplay** (or licensed stock) in `assets/broll/`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate one short (gradient background if no b-roll)
python -m faceless_shorts make

# Pick a topic
python -m faceless_shorts list-topics
python -m faceless_shorts make --topic day1-money

# Batch of 3
python -m faceless_shorts batch --count 3
```

Outputs land in:

- `output/<timestamp>_<topic>/` — working files (script, voice, mp4)
- `output/ready_to_post/<slug>/` — upload pack (`caption.txt`, `hashtags.txt`, `meta.json`, mp4)

## Add your own footage

Drop vertical or landscape clips into:

```text
assets/broll/*.mp4
```

Filenames containing `trailer`, `cutscene`, or `official_ost` are ignored (see `config.yaml` → `compliance`).

Optional: drop a `.ttf` into `assets/fonts/` for branded captions.

## YouTube auto-upload

1. Create a Google Cloud project → enable **YouTube Data API v3**.
2. Create OAuth client (Desktop app) → download JSON → save as `credentials/client_secret.json`.
3. In `config.yaml`:

```yaml
youtube:
  enabled: true
  privacy: private   # switch to public when confident
```

4. Run:

```bash
python -m faceless_shorts make --upload
```

First run opens a browser/console login and stores `credentials/youtube_token.json`.

Upload an already-rendered short:

```bash
python -m faceless_shorts upload \
  --video output/ready_to_post/SLUG/SLUG.mp4 \
  --script output/SLUG/script.json
```

## Smarter scripts (optional)

```bash
cp .env.example .env
# set OPENAI_API_KEY=...
```

```yaml
script:
  mode: openai
```

## Daily scheduler

```bash
python -m faceless_shorts schedule --once   # one batch now
python -m faceless_shorts schedule          # daily at scheduler.run_hour_local
```

## Money workflow this supports

1. Generate 1–3 shorts/day around launch.
2. Auto-upload to YouTube Shorts (ads later).
3. Manually (or via official APIs later) post the same pack to TikTok/Reels from `ready_to_post`.
4. Put affiliate links in bio / long-form descriptions.
5. Funnel Shorts viewers into a niche (money routes, map mistakes, settings).

## Commands

```text
python -m faceless_shorts list-topics
python -m faceless_shorts voices
python -m faceless_shorts make [--topic ID] [--upload|--no-upload] [--script-only]
python -m faceless_shorts batch --count N
python -m faceless_shorts upload --video PATH --script PATH
python -m faceless_shorts schedule [--once]
```

## Stack

- Python 3.12+, ffmpeg, edge-tts, Pillow, Click, PyYAML
- Google API client for YouTube OAuth upload

## Disclaimer

You are responsible for copyright, platform Terms of Service, FTC affiliate disclosures, and not uploading content you do not have rights to. This tool helps produce **original faceless commentary shorts** and upload them through **official APIs** where configured.
