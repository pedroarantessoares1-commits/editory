from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from app.engine import engine
from app.models import Job, Segment


MODELS = {
    "fast": {"model_size": "small", "beam_size": 1},
    "balanced": {"model_size": "large-v3-turbo", "beam_size": 3},
    "accurate": {"model_size": "large-v3", "beam_size": 5},
}


class CancelledJob(Exception):
    pass


def check_cancel(job: Job) -> None:
    if job.cancel_requested or job.status == "cancelled":
        raise CancelledJob("Tarefa cancelada.")


def has_cuda() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        pass

    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def extract_audio(input_path: Path, output_path: Path) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg nao encontrado no PATH.")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Falha ao converter audio com FFmpeg.")


def run_command(cmd: list[str], failure_message: str) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        details = result.stderr.strip().splitlines()
        summary = details[-1] if details else failure_message
        raise RuntimeError(summary)


def run_ffmpeg(input_path: Path, output_path: Path, extra_args: list[str]) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg nao encontrado no PATH.")

    cmd = ["ffmpeg", "-y", "-i", str(input_path), *extra_args, str(output_path)]
    run_command(cmd, "Falha ao processar audio com FFmpeg.")


def convert_to_mp3(input_path: Path, output_path: Path, light_cleanup: bool) -> None:
    run_ffmpeg(
        input_path,
        output_path,
        [
            "-vn",
            "-map",
            "0:a:0",
            "-threads",
            "0",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "5",
            "-compression_level",
            "0",
        ],
    )


def create_transcription_wav(input_path: Path, output_path: Path) -> None:
    run_ffmpeg(
        input_path,
        output_path,
        [
            "-vn",
            "-threads",
            "0",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-f",
            "wav",
        ],
    )


def run_deep_filter(input_path: Path, work_dir: Path) -> Path:
    deep_filter = shutil.which("deepFilter") or shutil.which("deep-filter")
    for tool_name in ("deepFilter.exe", "deep-filter.exe"):
        local_deep_filter = Path(sys.executable).parent / tool_name
        if deep_filter is None and local_deep_filter.exists():
            deep_filter = str(local_deep_filter)
    if deep_filter is None:
        raise RuntimeError(
            "DeepFilterNet nao esta instalado. Rode scripts/install.ps1 para instalar as dependencias opcionais."
        )

    out_dir = work_dir / "deepfilter"
    out_dir.mkdir(exist_ok=True)
    result = subprocess.run(
        [deep_filter, str(input_path), "-o", str(out_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Falha ao reduzir ruido com DeepFilterNet.")

    outputs = sorted(out_dir.glob("*.wav"))
    if not outputs:
        raise RuntimeError("DeepFilterNet nao gerou arquivo de audio.")
    return outputs[0]


def run_demucs(input_path: Path, work_dir: Path) -> Path:
    out_dir = work_dir / "demucs"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "demucs",
            "--two-stems",
            "vocals",
            "-n",
            "mdx_extra_q",
            "-o",
            str(out_dir),
            str(input_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Falha ao separar voz com Demucs.")

    matches = sorted(out_dir.glob("**/vocals.wav"))
    if not matches:
        raise RuntimeError("Demucs nao gerou a faixa de voz.")
    return matches[0]


def prepare_audio(job: Job, media_path: Path, work_dir: Path, update: Callable[[Job], None]) -> Path:
    check_cancel(job)
    job.status = "preparing"
    job.progress = 0.05
    job.message = "Preparando audio"
    update(job)

    prepared_source = media_path
    final_mp3 = work_dir / "audio.mp3"
    if not prepared_source.exists() and final_mp3.exists():
        prepared_source = final_mp3

    if job.settings.separate_voice:
        check_cancel(job)
        job.progress = 0.08
        job.message = "Separando voz da musica"
        update(job)
        prepared_source = run_demucs(prepared_source, work_dir)

    if job.settings.deep_noise_cleanup:
        check_cancel(job)
        job.progress = 0.1
        job.message = "Reduzindo ruido pesado"
        update(job)
        prepared_source = run_deep_filter(prepared_source, work_dir)

    check_cancel(job)
    job.progress = 0.14
    job.message = "Convertendo para MP3 rapido"
    update(job)
    if prepared_source.resolve() == final_mp3.resolve():
        pass
    elif prepared_source.suffix.lower() == ".mp3":
        shutil.copy2(prepared_source, final_mp3)
    elif not final_mp3.exists():
        convert_to_mp3(prepared_source, final_mp3, job.settings.light_cleanup)

    if (
        media_path.exists()
        and media_path.resolve().is_relative_to(work_dir.resolve())
        and media_path.resolve() != final_mp3.resolve()
    ):
        media_path.unlink(missing_ok=True)

    job.audio_filename = final_mp3.name
    job.audio_url = f"/api/jobs/{job.id}/audio"
    job.progress = 0.18
    job.message = "Audio pronto para transcricao"
    update(job)
    return final_mp3


def transcribe(job: Job, media_path: Path, work_dir: Path, update: Callable[[Job], None]) -> Job:
    profile = MODELS.get(job.settings.mode, MODELS["balanced"])

    check_cancel(job)
    audio_path = prepare_audio(job, media_path, work_dir, update)

    check_cancel(job)
    job.status = "processing"
    job.progress = 0.22
    job.message = "Aguardando motor de transcricao"
    update(job)

    job.progress = 0.3
    job.message = "Transcrevendo"
    update(job)

    collected: list[Segment] = []

    def on_segment(index: int, seg: object) -> None:
        check_cancel(job)
        collected.append(
            Segment(
                id=index,
                start=float(seg.start),
                end=float(seg.end),
                text=seg.text.strip(),
            )
        )
        if job.duration:
            job.progress = min(0.95, max(job.progress, float(seg.end) / job.duration))
        else:
            job.progress = min(0.95, job.progress + 0.02)
        job.segments = collected
        job.text = " ".join(s.text for s in collected).strip()
        job.message = f"Transcrevendo trecho {index}"
        update(job)

    def reset_segments() -> None:
        check_cancel(job)
        collected.clear()
        job.segments = []
        job.text = ""
        job.progress = 0.3
        job.message = "GPU indisponivel, repetindo transcricao em CPU"
        update(job)

    try:
        _, info = engine.transcribe_audio(
            str(audio_path),
            model_size=profile["model_size"],
            language=job.settings.language or None,
            task=job.settings.task,
            beam_size=profile["beam_size"],
            vad_filter=job.settings.vad_filter,
            initial_prompt=job.settings.prompt or None,
            progress=on_segment,
            reset=reset_segments,
        )
    except CancelledJob:
        if audio_path.name != job.audio_filename:
            audio_path.unlink(missing_ok=True)
        raise

    job.duration = getattr(info, "duration", None)
    job.detected_language = getattr(info, "language", None)

    job.status = "done"
    job.progress = 1.0
    job.message = "Concluido"
    job.segments = collected
    job.text = " ".join(s.text for s in collected).strip()
    update(job)
    if audio_path.name != job.audio_filename:
        audio_path.unlink(missing_ok=True)
    return job
