from __future__ import annotations

import math
import shutil
import subprocess
import wave
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

import numpy as np

from app.models import JobStatus, SilenceTask


SAMPLE_RATE = 16000
FRAME_MS = 25


@dataclass(frozen=True)
class SilenceProfile:
    cut_after: float
    target_pause: float
    min_speech_ms: int
    min_silence_ms: int
    vad_threshold: float
    leading_pad: float
    trailing_pad: float
    volume_margin_db: float


@dataclass(frozen=True)
class VolumeDetection:
    intervals: list[tuple[float, float]]
    threshold_db: float
    noise_db: float
    speech_db: float


PROFILES = {
    "suave": SilenceProfile(
        cut_after=1.2,
        target_pause=0.55,
        min_speech_ms=180,
        min_silence_ms=450,
        vad_threshold=0.42,
        leading_pad=0.3,
        trailing_pad=0.38,
        volume_margin_db=8.5,
    ),
    "normal": SilenceProfile(
        cut_after=0.8,
        target_pause=0.32,
        min_speech_ms=150,
        min_silence_ms=280,
        vad_threshold=0.38,
        leading_pad=0.24,
        trailing_pad=0.3,
        volume_margin_db=7.0,
    ),
    "agressivo": SilenceProfile(
        cut_after=0.45,
        target_pause=0.16,
        min_speech_ms=110,
        min_silence_ms=160,
        vad_threshold=0.34,
        leading_pad=0.16,
        trailing_pad=0.22,
        volume_margin_db=5.2,
    ),
}


class CancelledSilenceTask(Exception):
    pass


def check_cancel(task: SilenceTask) -> None:
    if task.cancel_requested or task.status == JobStatus.cancelled:
        raise CancelledSilenceTask("Tarefa cancelada.")


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg nao encontrado no PATH.")


def probe_duration(path: Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def run_ffmpeg(args: list[str]) -> None:
    ensure_ffmpeg()
    result = subprocess.run(["ffmpeg", "-y", *args], capture_output=True, text=True)
    if result.returncode != 0:
        details = result.stderr.strip().splitlines()
        raise RuntimeError(details[-1] if details else "Falha ao processar audio.")


def create_analysis_wav(input_path: Path, output_path: Path) -> None:
    run_ffmpeg(
        [
            "-i",
            str(input_path),
            "-vn",
            "-threads",
            "0",
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-af",
            "highpass=f=70,lowpass=f=7800",
            "-f",
            "wav",
            str(output_path),
        ]
    )


@lru_cache(maxsize=1)
def silero_model():
    from silero_vad import load_silero_vad

    return load_silero_vad()


def detect_with_silero(wav_path: Path, profile: SilenceProfile) -> list[tuple[float, float]]:
    from silero_vad import get_speech_timestamps, read_audio

    wav = read_audio(str(wav_path), sampling_rate=SAMPLE_RATE)
    timestamps = get_speech_timestamps(
        wav,
        silero_model(),
        threshold=profile.vad_threshold,
        sampling_rate=SAMPLE_RATE,
        min_speech_duration_ms=profile.min_speech_ms,
        min_silence_duration_ms=profile.min_silence_ms,
        speech_pad_ms=0,
        return_seconds=True,
    )
    return [(float(item["start"]), float(item["end"])) for item in timestamps]


def detect_with_auditok(wav_path: Path, profile: SilenceProfile) -> list[tuple[float, float]]:
    import auditok

    events = auditok.split(
        str(wav_path),
        min_dur=max(profile.min_speech_ms / 1000, 0.1),
        max_dur=None,
        max_silence=min(profile.cut_after, 0.35),
        max_leading_silence=0.12,
        max_trailing_silence=0.18,
        strict_min_dur=False,
    )
    return [(float(event.start), float(event.end)) for event in events]


def read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        rate = source.getframerate()
        frames = source.readframes(source.getnframes())

    if sample_width != 2:
        raise RuntimeError("WAV temporario precisa estar em PCM 16-bit.")

    audio = np.frombuffer(frames, dtype=np.int16)
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)
    return audio.astype(np.float32) / 32768.0, rate


def moving_average(values: np.ndarray, size: int) -> np.ndarray:
    if size <= 1 or values.size < size:
        return values
    kernel = np.ones(size, dtype=np.float32) / size
    return np.convolve(values, kernel, mode="same")


def intervals_from_active(active: np.ndarray, duration: float, max_gap_s: float, min_active_s: float) -> list[tuple[float, float]]:
    frame_s = FRAME_MS / 1000
    max_gap = max(1, int(max_gap_s / frame_s))
    min_active = max(1, int(min_active_s / frame_s))
    intervals: list[tuple[float, float]] = []
    start: int | None = None
    last_active: int | None = None
    gap = 0

    for index, is_active in enumerate(active):
        if is_active:
            if start is None:
                start = index
            last_active = index
            gap = 0
            continue
        if start is not None:
            gap += 1
            if gap > max_gap:
                end = last_active if last_active is not None else index
                if end - start + 1 >= min_active:
                    intervals.append((start * frame_s, min(duration, (end + 1) * frame_s)))
                start = None
                last_active = None
                gap = 0

    if start is not None and last_active is not None and last_active - start + 1 >= min_active:
        intervals.append((start * frame_s, min(duration, (last_active + 1) * frame_s)))
    return intervals


def active_ratio(intervals: list[tuple[float, float]], duration: float) -> float:
    if duration <= 0:
        return 0.0
    total = sum(max(0.0, end - start) for start, end in intervals)
    return total / duration


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def detect_with_volume(wav_path: Path, profile: SilenceProfile, strategy: str) -> VolumeDetection:
    audio, rate = read_wav_mono(wav_path)
    duration = len(audio) / rate if rate else 0.0
    if not audio.size or duration <= 0:
        return VolumeDetection([], -60.0, -90.0, -90.0)

    frame_size = max(1, int(rate * FRAME_MS / 1000))
    frame_count = math.ceil(len(audio) / frame_size)
    padded = np.pad(audio, (0, frame_count * frame_size - len(audio)))
    frames = padded.reshape(frame_count, frame_size)
    rms = np.sqrt(np.mean(np.square(frames), axis=1) + 1e-12)
    db = 20 * np.log10(np.maximum(rms, 1e-8))
    smooth_db = moving_average(db, 5)

    p20 = float(np.percentile(smooth_db, 20))
    p45 = float(np.percentile(smooth_db, 45))
    p60 = float(np.percentile(smooth_db, 60))
    p85 = float(np.percentile(smooth_db, 85))
    noise_db = p20
    speech_db = p85

    margin = profile.volume_margin_db
    if strategy == "volume_agressivo":
        margin -= 1.8
    threshold = clamp(noise_db + margin, -62.0, min(speech_db - 4.0, -18.0))
    if p85 - p20 > 12:
        threshold = max(threshold, p45 if strategy == "volume_agressivo" else p45 - 2.0)
    if strategy == "volume_agressivo":
        threshold = max(threshold, p60 - 3.0)

    max_gap_s = min(profile.cut_after * 0.45, 0.28)
    min_active_s = max(profile.min_speech_ms / 1000, 0.08)
    intervals = intervals_from_active(smooth_db >= threshold, duration, max_gap_s, min_active_s)

    ratio = active_ratio(intervals, duration)
    if ratio > 0.96 and p85 - p20 > 9:
        threshold = max(threshold, p60 - (2.0 if strategy == "volume_agressivo" else 4.0))
        intervals = intervals_from_active(smooth_db >= threshold, duration, max_gap_s, min_active_s)

    return VolumeDetection(intervals, round(threshold, 1), round(noise_db, 1), round(speech_db, 1))


def detection_is_useful(intervals: list[tuple[float, float]], duration: float, max_ratio: float = 0.985) -> bool:
    ratio = active_ratio(intervals, duration)
    return 0.015 <= ratio <= max_ratio


def merge_intervals(intervals: list[tuple[float, float]], join_gap: float) -> list[tuple[float, float]]:
    merged: list[tuple[float, float]] = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if not merged or start - merged[-1][1] > join_gap:
            merged.append((start, end))
            continue
        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def padded_intervals(
    intervals: list[tuple[float, float]],
    duration: float,
    leading: float,
    trailing: float,
) -> list[tuple[float, float]]:
    return merge_intervals(
        [(max(0.0, start - leading), min(duration, end + trailing)) for start, end in intervals],
        join_gap=0.05,
    )


def normalize_pauses(
    intervals: list[tuple[float, float]],
    duration: float,
    profile: SilenceProfile,
    preserve_edges: bool,
) -> tuple[list[tuple[float, float]], int]:
    if not intervals:
        return [(0.0, duration)], 0

    leading = profile.leading_pad if preserve_edges else 0.05
    trailing = profile.trailing_pad if preserve_edges else 0.05
    padded = padded_intervals(intervals, duration, leading, trailing)

    keep: list[tuple[float, float]] = [padded[0]]
    cuts = 0
    for start, end in padded[1:]:
        previous_start, previous_end = keep[-1]
        gap = start - previous_end
        if gap <= profile.cut_after:
            keep[-1] = (previous_start, max(previous_end, end))
            continue

        cuts += 1
        keep_extra_each_side = profile.target_pause / 2
        keep[-1] = (previous_start, min(duration, previous_end + keep_extra_each_side))
        adjusted_start = max(0.0, start - keep_extra_each_side)
        if adjusted_start <= keep[-1][1]:
            keep[-1] = (previous_start, max(keep[-1][1], end))
        else:
            keep.append((adjusted_start, end))

    return merge_intervals(keep, join_gap=0.02), cuts


def concat_line(path: Path) -> str:
    return "file '{}'\n".format(str(path.resolve()).replace("\\", "/").replace("'", "'\\''"))


def render_intervals(source_path: Path, output_path: Path, intervals: list[tuple[float, float]], work_dir: Path) -> None:
    chunks_dir = work_dir / "chunks"
    if chunks_dir.exists():
        shutil.rmtree(chunks_dir)
    chunks_dir.mkdir()

    concat_file = chunks_dir / "chunks.txt"
    with concat_file.open("w", encoding="utf-8") as out:
        for index, (start, end) in enumerate(intervals, start=1):
            chunk = chunks_dir / f"chunk_{index:05d}.wav"
            run_ffmpeg(
                [
                    "-i",
                    str(source_path),
                    "-vn",
                    "-ss",
                    f"{start:.3f}",
                    "-to",
                    f"{end:.3f}",
                    "-threads",
                    "0",
                    "-ac",
                    "2",
                    "-ar",
                    "44100",
                    "-codec:a",
                    "pcm_s16le",
                    str(chunk),
                ]
            )
            out.write(concat_line(chunk))

    run_ffmpeg(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-threads",
            "0",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output_path),
        ]
    )


def choose_intervals(
    wav_path: Path,
    profile: SilenceProfile,
    strategy: str,
    duration: float,
    preserve_edges: bool,
) -> tuple[list[tuple[float, float]], str, float | None]:
    silero_intervals: list[tuple[float, float]] = []
    try:
        silero_intervals = detect_with_silero(wav_path, profile)
    except Exception:
        silero_intervals = []

    if strategy == "voz_protegida":
        if detection_is_useful(silero_intervals, duration):
            return silero_intervals, "voz-protegida/silero-vad", None
        try:
            fallback = detect_with_auditok(wav_path, profile)
            if detection_is_useful(fallback, duration):
                return fallback, "voz-protegida/auditok", None
        except Exception:
            pass

    detection = detect_with_volume(wav_path, profile, strategy)
    intervals = detection.intervals
    engine = "volume-agressivo" if strategy == "volume_agressivo" else "inteligente/volume-adaptativo"

    if not detection_is_useful(intervals, duration):
        try:
            fallback = detect_with_auditok(wav_path, profile)
            if detection_is_useful(fallback, duration):
                return fallback, f"{engine}+auditok", detection.threshold_db
        except Exception:
            pass

    silero_ratio = active_ratio(silero_intervals, duration)
    if preserve_edges and strategy != "volume_agressivo" and detection_is_useful(silero_intervals, duration, max_ratio=0.92):
        protected = padded_intervals(silero_intervals, duration, profile.leading_pad, profile.trailing_pad)
        intervals = merge_intervals([*intervals, *protected], join_gap=0.04)
        engine = f"{engine}+silero-protecao"
    elif preserve_edges and strategy == "volume_agressivo" and 0.02 <= silero_ratio <= 0.75:
        protected = padded_intervals(silero_intervals, duration, 0.08, 0.12)
        intervals = merge_intervals([*intervals, *protected], join_gap=0.04)
        engine = f"{engine}+bordas-silero"

    if not intervals:
        intervals = [(0.0, duration)]
    return intervals, engine, detection.threshold_db


def remove_silence(
    task: SilenceTask,
    input_path: Path,
    work_dir: Path,
    update: Callable[[SilenceTask], None],
) -> SilenceTask:
    profile = PROFILES.get(task.settings.profile, PROFILES["normal"])
    strategy = task.settings.strategy if task.settings.strategy in {"inteligente", "voz_protegida", "volume_agressivo"} else "inteligente"

    check_cancel(task)
    task.status = JobStatus.processing
    task.progress = 0.08
    task.message = "Analisando duracao"
    task.duration_original = probe_duration(input_path)
    update(task)

    source_path = input_path
    if task.settings.separate_voice:
        check_cancel(task)
        task.progress = 0.14
        task.message = "Separando voz da musica"
        update(task)
        from app.transcriber import run_demucs

        source_path = run_demucs(input_path, work_dir)

    check_cancel(task)
    analysis_wav = work_dir / "silence-analysis.wav"
    task.progress = 0.22
    task.message = "Preparando audio para deteccao"
    update(task)
    create_analysis_wav(source_path, analysis_wav)
    duration = probe_duration(analysis_wav) or task.duration_original or 0.0

    check_cancel(task)
    task.progress = 0.38
    task.message = "Detectando pausas com volume adaptativo"
    update(task)
    intervals, engine, threshold_db = choose_intervals(
        analysis_wav,
        profile,
        strategy,
        duration,
        task.settings.preserve_edges,
    )
    task.engine = engine
    task.threshold_db_used = threshold_db

    check_cancel(task)
    keep_intervals, cuts = normalize_pauses(intervals, duration, profile, task.settings.preserve_edges)
    task.kept_segments = len(keep_intervals)
    task.silence_cuts = cuts
    task.progress = 0.68
    task.message = f"Renderizando {task.kept_segments} trecho(s)"
    update(task)

    output_path = work_dir / "sem-silencio.mp3"
    render_intervals(source_path, output_path, keep_intervals, work_dir)

    check_cancel(task)
    task.output_filename = output_path.name
    task.audio_url = f"/api/silence/{task.id}/audio"
    task.duration_output = probe_duration(output_path)
    if task.duration_original and task.duration_output is not None and task.duration_original > 0:
        removed_seconds = max(0.0, task.duration_original - task.duration_output)
        task.removed_seconds = round(removed_seconds, 2)
        removed = max(0.0, min(100.0, (removed_seconds / task.duration_original) * 100))
        task.removed_percent = round(removed, 1)
    task.progress = 1.0
    task.status = JobStatus.done
    task.message = "Concluido"
    update(task)
    analysis_wav.unlink(missing_ok=True)
    return task
