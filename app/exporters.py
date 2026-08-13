from __future__ import annotations

import json
from typing import Iterable

from app.models import Job, Segment


def fmt_clock(seconds: float, sep: str = ",") -> str:
    millis = int(round((seconds - int(seconds)) * 1000))
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{millis:03d}"


def export_txt(job: Job) -> str:
    if not job.segments:
        return job.text.strip()
    lines = []
    for seg in job.segments:
        stamp = f"[{fmt_clock(seg.start, ':')} - {fmt_clock(seg.end, ':')}]"
        speaker = f"{seg.speaker}: " if seg.speaker else ""
        lines.append(f"{stamp} {speaker}{seg.text.strip()}")
    return "\n".join(lines).strip()


def export_srt(segments: Iterable[Segment]) -> str:
    blocks = []
    for i, seg in enumerate(segments, start=1):
        text = seg.text.strip()
        blocks.append(
            f"{i}\n{fmt_clock(seg.start)} --> {fmt_clock(seg.end)}\n{text}"
        )
    return "\n\n".join(blocks).strip() + "\n"


def export_vtt(segments: Iterable[Segment]) -> str:
    blocks = ["WEBVTT\n"]
    for seg in segments:
        text = seg.text.strip()
        blocks.append(f"{fmt_clock(seg.start, '.')} --> {fmt_clock(seg.end, '.')}\n{text}")
    return "\n\n".join(blocks).strip() + "\n"


def export_json(job: Job) -> str:
    return json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2)

