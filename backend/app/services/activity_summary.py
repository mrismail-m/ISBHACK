"""Compute writing evidence from raw events, never from client percentages."""

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.schemas.activity import NON_EDIT, ActivityEvents, ActivitySummary


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def iso(value: datetime) -> str:
    return utc(value).isoformat().replace("+00:00", "Z")


def summarize_activity(
    submission_id: str,
    activity: ActivityEvents,
    paste_flag_chars: int = 500,
    bucket: Literal["auto", "minute", "hour"] = "auto",
) -> ActivitySummary:
    starts = {s.session_id: utc(s.started_at) for s in activity.sessions}
    events = sorted(activity.events, key=lambda e: (starts[e.session_id], e.session_id, e.seq))
    doc = b""
    tags: list[str | None] = []  # None is typed/restored, otherwise paste source id.
    cuts: dict[str, str] = {}
    chunks: list[dict] = []
    edits: list[tuple[datetime, int, int]] = []
    inserted_total = deleted_total = 0
    times: list[datetime] = []
    for event in events:
        at = starts[event.session_id] + timedelta(milliseconds=event.t)
        times.append(at)
        if event.k in NON_EDIT:
            continue
        from_, to = event.from_, event.to
        if not 0 <= from_ <= to <= len(doc) // 2:
            raise ValueError(f"Event {event.session_id}:{event.seq} has an invalid UTF-16 range")
        text = event.text
        trimmed = text.strip()
        internal = (
            event.k == "paste"
            and len(trimmed.encode("utf-16-le")) // 2 >= 20
            and (
                trimmed in doc.decode("utf-16-le", errors="surrogatepass")
                or trimmed == cuts.get(event.session_id)
            )
        )
        if event.k == "cut":
            cuts[event.session_id] = (
                doc[from_ * 2 : to * 2].decode("utf-16-le", errors="surrogatepass").strip()
            )
        inserted = text.encode("utf-16-le", errors="surrogatepass")
        count = len(inserted) // 2
        pasted = event.k in {"paste", "drop"} and not internal
        source = f"{event.session_id}:{event.seq}" if pasted else None
        tags[from_:to] = [source] * count
        doc = doc[: from_ * 2] + inserted + doc[to * 2 :]
        inserted_total += count
        deleted_total += to - from_
        edits.append((at, 0 if pasted else count, count if pasted else 0))
        if pasted and count >= 40:
            chunks.append(
                {
                    "session_id": event.session_id,
                    "event_seq": event.seq,
                    "at": iso(at),
                    "t": event.t,
                    "chars": count,
                    "major": count >= paste_flag_chars,
                    "declared_source": None,
                }
            )
    survival = Counter(tags)
    for chunk in chunks:
        survived = survival[f"{chunk['session_id']}:{chunk['event_seq']}"]
        chunk.update(
            survived_chars=survived, survived_pct=round(survived / chunk["chars"] * 100, 1)
        )
    span = (max(times) - min(times)).total_seconds() / 60 if times else 0
    selected = ("hour" if span > 180 else "minute") if bucket == "auto" else bucket
    buckets: dict[datetime, dict] = {}
    active = set()
    for at, typed, pasted in edits:
        minute = at.replace(second=0, microsecond=0)
        active.add(minute)
        start = minute.replace(minute=0) if selected == "hour" else minute
        row = buckets.setdefault(
            start,
            {
                "bucket_start": iso(start),
                "edits": 0,
                "typed_chars": 0,
                "pasted_chars": 0,
            },
        )
        row["edits"] += 1
        row["typed_chars"] += typed
        row["pasted_chars"] += pasted
    final_chars = len(tags)
    pasted_chars = sum(tag is not None for tag in tags)
    pasted_pct = round(pasted_chars / final_chars * 100, 1) if final_chars else 0.0
    return ActivitySummary(
        submission_id=submission_id,
        final_chars=final_chars,
        typed_pct=round(100 - pasted_pct, 1) if final_chars else 0.0,
        pasted_pct=pasted_pct,
        paste_chunks=chunks,
        revision_ratio=round(deleted_total / inserted_total, 3) if inserted_total else 0.0,
        active_minutes=len(active),
        span_minutes=round(span, 1),
        tab_switches=sum(e.k == "hidden" for e in events),
        sessions=len(activity.sessions),
        bucket=selected,
        heatmap=[buckets[k] for k in sorted(buckets)],
    )
