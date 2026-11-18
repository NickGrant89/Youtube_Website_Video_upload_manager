"""Curated GTA 6 faceless-short topic bank + hooks."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    id: str
    hook: str
    angle: str
    points: tuple[str, ...]
    hashtags: tuple[str, ...]


TOPIC_BANK: list[Topic] = [
    Topic(
        id="day1-money",
        hook="Stop grinding wrong on day one in GTA 6.",
        angle="First-session money priorities for beginners",
        points=(
            "Do the early story beats that unlock better payouts before random freeroam grind.",
            "Sell junk fast, keep high-value gear, and avoid blowing cash on flash cars early.",
            "Mark one side hustle loop you can repeat in under ten minutes.",
        ),
        hashtags=("GTA6", "GTAVI", "GTATips", "GamingShorts", "ViceCity"),
    ),
    Topic(
        id="map-mistakes",
        hook="These map mistakes will waste your first week in GTA 6.",
        angle="Exploration mistakes new players make",
        points=(
            "Don't chase every icon before you unlock travel shortcuts.",
            "Learn one safe district loop instead of crossing the whole map empty-handed.",
            "Screenshot key vendors the first time you find them.",
        ),
        hashtags=("GTA6", "GTAMap", "GTAGuide", "Shorts", "Gaming"),
    ),
    Topic(
        id="wanted-stars",
        hook="Wanted stars are not the real problem. Panic is.",
        angle="Police / wanted-level survival basics",
        points=(
            "Break line of sight before you sprint into a dead end.",
            "Change vehicles after a chase, not during the hottest pursuit.",
            "Know one lose-cops route near your usual grind spot.",
        ),
        hashtags=("GTA6", "GTAGameplay", "TipsAndTricks", "GamingShorts"),
    ),
    Topic(
        id="inventory-rules",
        hook="Your inventory decisions decide if you stay broke.",
        angle="Loot and inventory discipline",
        points=(
            "Carry what sells, not what looks cool.",
            "Empty junk before big missions so you never leave money on the ground.",
            "Keep one emergency kit slot — ammo, snacks, or armor.",
        ),
        hashtags=("GTA6", "GTATips", "BeginnerGuide", "Shorts"),
    ),
    Topic(
        id="car-trap",
        hook="Buying the wrong car early is a wealth trap.",
        angle="Vehicle spending advice",
        points=(
            "Prioritize reliability and storage over flex for the first days.",
            "Insurance and repairs can wipe a night of progress.",
            "Earn a repeatable income loop before the garage flex.",
        ),
        hashtags=("GTA6", "GTACars", "MoneyTips", "Gaming"),
    ),
    Topic(
        id="mission-order",
        hook="Mission order matters more than people think.",
        angle="Story pacing for better unlocks",
        points=(
            "Front-load missions that open tools, areas, or better payouts.",
            "Don't burn hours on low-pay side content before key unlocks.",
            "Track what each mission actually unlocks, not just the cutscene hype.",
        ),
        hashtags=("GTA6", "StoryGuide", "GTAVI", "Shorts"),
    ),
    Topic(
        id="duo-roles",
        hook="If you play GTA 6 with a friend, split roles or stay broke.",
        angle="Co-op efficiency",
        points=(
            "One player drives and escapes, one handles objectives and loot.",
            "Share a callout language for cops, ammo, and exits.",
            "Split sell runs so neither inventory bricks the payout.",
        ),
        hashtags=("GTA6", "Coop", "GTAWithFriends", "GamingShorts"),
    ),
    Topic(
        id="settings-edge",
        hook="These settings give you a quiet edge in GTA 6.",
        angle="QoL / control settings worth changing first",
        points=(
            "Tune aim assist and camera speed before your first tough shootout.",
            "Raise key UI prompts you actually use; hide clutter you ignore.",
            "Bind a panic button for phone, map, or weapon wheel.",
        ),
        hashtags=("GTA6", "Settings", "FPSTips", "Gaming"),
    ),
    Topic(
        id="lore-hook",
        hook="Vice City is not just nostalgia — it's a money map.",
        angle="Lore-flavored practical tip",
        points=(
            "Tourist strips mean dense NPCs, denser opportunity, and denser heat.",
            "Learn which districts feel rich versus which districts feel watched.",
            "Treat landmarks as navigation anchors for faster grind loops.",
        ),
        hashtags=("GTA6", "ViceCity", "GTALore", "Shorts"),
    ),
    Topic(
        id="launch-week",
        hook="Launch week GTA 6 players lose hours to the wrong grind.",
        angle="Launch-week focus plan",
        points=(
            "Day one: unlock movement and income tools, not cosmetics.",
            "Day two: build one repeatable loop you could run half-asleep.",
            "Day three: only then expand into exploration and flex purchases.",
        ),
        hashtags=("GTA6", "LaunchWeek", "GTAGuide", "GamingShorts"),
    ),
]


DEFAULT_HASHTAGS = (
    "GTA6",
    "GTAVI",
    "GTA",
    "GamingShorts",
    "FacelessCreators",
    "ViceCity",
)


def pick_topic(topic_id: str | None = None) -> Topic:
    if topic_id:
        for topic in TOPIC_BANK:
            if topic.id == topic_id:
                return topic
        raise ValueError(f"Unknown topic id: {topic_id}. Use --list-topics.")
    return random.choice(TOPIC_BANK)


def list_topics() -> list[Topic]:
    return list(TOPIC_BANK)