"""Upload finished Shorts via the official YouTube Data API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .script_generator import ScriptPackage


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _load_youtube_service(cfg: dict[str, Any]):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google API packages missing. Run: pip install -r requirements.txt"
        ) from exc

    yt_cfg = cfg.get("youtube") or {}
    root = Path(cfg["_root"])
    client_secrets = root / yt_cfg.get("client_secrets", "credentials/client_secret.json")
    token_file = root / yt_cfg.get("token_file", "credentials/youtube_token.json")

    if not client_secrets.exists():
        raise FileNotFoundError(
            f"Missing {client_secrets}. Download OAuth client JSON from Google Cloud Console "
            "(YouTube Data API v3) and save it there."
        )

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
            # run_local_server works on machines with a browser; console fallback otherwise
            try:
                creds = flow.run_local_server(port=0)
            except Exception:
                creds = flow.run_console()
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: Path,
    script: ScriptPackage,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    from googleapiclient.http import MediaFileUpload

    yt_cfg = cfg.get("youtube") or {}
    if not yt_cfg.get("enabled", False):
        raise RuntimeError("YouTube upload disabled. Set youtube.enabled: true in config.yaml")

    youtube = _load_youtube_service(cfg)
    tags = list(dict.fromkeys([*(yt_cfg.get("tags") or []), *script.hashtags]))
    body = {
        "snippet": {
            "title": script.title[:100],
            "description": script.description[:4900],
            "tags": tags[:30],
            "categoryId": str(yt_cfg.get("category_id", "20")),
        },
        "status": {
            "privacyStatus": yt_cfg.get("privacy", "private"),
            "selfDeclaredMadeForKids": bool(yt_cfg.get("made_for_kids", False)),
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response.get("id")
    result = {
        "platform": "youtube",
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}" if video_id else None,
        "privacy": body["status"]["privacyStatus"],
        "title": body["snippet"]["title"],
    }
    return result


def save_upload_receipt(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")