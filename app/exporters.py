from __future__ import annotations

import json
import re
import textwrap
from typing import Iterable

from app.models import Job, Segment


def fmt_clock(seconds: float, sep: str = ",") -> str:
    seconds = max(0.0, float(seconds))
    total_millis = int(round(seconds * 1000))
    total, millis = divmod(total_millis, 1000)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{millis:03d}"


def wrap_subtitle_text(text: str, width: int = 42, max_lines: int = 2) -> str:
    words = re.sub(r"\s+", " ", text).strip().split(" ")
    if not words or words == [""]:
        return ""

    wrapped = textwrap.wrap(" ".join(words), width=width, break_long_words=False, break_on_hyphens=False)
    if len(wrapped) <= max_lines:
        return "\n".join(wrapped)

    midpoint = max(1, len(words) // 2)
    best_index = midpoint
    best_score = float("inf")
    for index in range(1, len(words)):
        left = " ".join(words[:index])
        right = " ".join(words[index:])
        score = abs(len(left) - len(right))
        if score < best_score:
            best_score = score
            best_index = index
    return "\n".join([" ".join(words[:best_index]), " ".join(words[best_index:])])


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
    index = 1
    for seg in segments:
        text = wrap_subtitle_text(seg.text)
        if not text:
            continue
        start = max(0.0, float(seg.start))
        end = max(start + 0.001, float(seg.end))
        blocks.append(
            f"{index}\n{fmt_clock(start)} --> {fmt_clock(end)}\n{text}"
        )
        index += 1
    return "\r\n\r\n".join(blocks).strip() + "\r\n"


def export_vtt(segments: Iterable[Segment]) -> str:
    blocks = ["WEBVTT\n"]
    for seg in segments:
        text = seg.text.strip()
        blocks.append(f"{fmt_clock(seg.start, '.')} --> {fmt_clock(seg.end, '.')}\n{text}")
    return "\n\n".join(blocks).strip() + "\n"


def export_json(job: Job) -> str:
    return json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2)
