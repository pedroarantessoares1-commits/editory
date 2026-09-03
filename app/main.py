from __future__ import annotations

import asyncio
import re
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.engine import engine
from app.exporters import export_srt
from app.models import Job, JobSettings, JobStatus, SilenceSettings, SilenceTask
from app.silence import CancelledSilenceTask, remove_silence
from app.transcriber import CancelledJob, has_cuda, transcribe


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
JOBS = DATA / "jobs"
SILENCE = DATA / "silence"
STATIC = ROOT / "web"

for folder in (UPLOADS, JOBS, SILENCE):
    folder.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Editory", version="0.5.2-alpha")
jobs: dict[str, Job] = {}
silence_tasks: dict[str, SilenceTask] = {}
lock = asyncio.Lock()
silence_lock = asyncio.Lock()
warmup_lock = asyncio.Lock()


def has_active_jobs() -> bool:
    active = {JobStatus.queued, JobStatus.preparing, JobStatus.processing}
    return any(job.status in active for job in jobs.values()) or any(task.status in active for task in silence_tasks.values())


def job_dir(job_id: str) -> Path:
    path = JOBS / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def silence_dir(task_id: str) -> Path:
    path = SILENCE / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_jobs() -> None:
    for path in JOBS.glob("*/job.json"):
        try:
            job = Job.model_validate_json(path.read_text(encoding="utf-8"))
            if job.status in {JobStatus.queued, JobStatus.preparing, JobStatus.processing}:
                job.status = JobStatus.failed
                job.message = "Interrompido ao fechar o app"
                job.error = job.error or "Este job foi interrompido antes de concluir. Envie o arquivo novamente."
                path.write_text(job.model_dump_json(indent=2), encoding="utf-8")
            jobs[job.id] = job
        except Exception:
            continue


def load_silence_tasks() -> None:
    for path in SILENCE.glob("*/task.json"):
        try:
            task = SilenceTask.model_validate_json(path.read_text(encoding="utf-8"))
            if task.status in {JobStatus.queued, JobStatus.preparing, JobStatus.processing}:
                task.status = JobStatus.failed
                task.message = "Interrompido ao fechar o app"
                task.error = task.error or "Esta tarefa foi interrompida antes de concluir. Tente novamente."
                path.write_text(task.model_dump_json(indent=2), encoding="utf-8")
            silence_tasks[task.id] = task
        except Exception:
            continue


def save_job(job: Job) -> None:
    job_dir(job.id).joinpath("job.json").write_text(
        job.model_dump_json(indent=2), encoding="utf-8"
    )
    jobs[job.id] = job


def save_silence_task(task: SilenceTask) -> None:
    silence_dir(task.id).joinpath("task.json").write_text(
        task.model_dump_json(indent=2), encoding="utf-8"
    )
    silence_tasks[task.id] = task


def srt_filename(filename: str) -> str:
    stem = Path(filename).stem.strip() or "legenda"
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", stem)
    stem = stem.rstrip(" .") or "legenda"
    return f"{stem}.srt"


async def run_job(job_id: str, media_path: Path) -> None:
    async with lock:
        engine.touch()
        job = jobs[job_id]
        try:
            await asyncio.to_thread(transcribe, job, media_path, job_dir(job_id), save_job)
        except CancelledJob as exc:
            job.status = JobStatus.cancelled
            job.progress = job.progress or 0.0
            job.error = str(exc)
            job.message = "Cancelado"
            save_job(job)
        except Exception as exc:
            job.status = JobStatus.failed
            job.error = str(exc)
            job.message = "Falhou"
            save_job(job)


async def run_silence_task(task_id: str, media_path: Path) -> None:
    async with silence_lock:
        task = silence_tasks[task_id]
        try:
            await asyncio.to_thread(remove_silence, task, media_path, silence_dir(task_id), save_silence_task)
        except CancelledSilenceTask as exc:
            task.status = JobStatus.cancelled
            task.error = str(exc)
            task.message = "Cancelado"
            save_silence_task(task)
        except Exception as exc:
            task.status = JobStatus.failed
            task.error = str(exc)
            task.message = "Falhou"
            save_silence_task(task)


def retry_source(job_id: str) -> Path:
    path = job_dir(job_id)
    for candidate in path.glob("original.*"):
        if candidate.is_file():
            return candidate
    audio = path / "audio.mp3"
    if audio.exists():
        return audio
    raise HTTPException(status_code=404, detail="Arquivo de audio/video nao encontrado para retentar.")


def silence_source(task_id: str) -> Path:
    task = get_silence_task(task_id)
    if task.input_filename:
        candidate = silence_dir(task_id) / task.input_filename
        if candidate.exists():
            return candidate
    for candidate in silence_dir(task_id).glob("input.*"):
        if candidate.is_file():
            return candidate
    raise HTTPException(status_code=404, detail="Audio nao encontrado para retentar.")


@app.on_event("startup")
async def startup() -> None:
    load_jobs()
    load_silence_tasks()
    asyncio.create_task(standby_monitor())


async def standby_monitor() -> None:
    while True:
        await asyncio.sleep(60)
        await asyncio.to_thread(engine.maybe_standby, has_active_jobs())


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "cuda": has_cuda(),
        "storage": str(DATA),
    }


@app.get("/api/engine")
def engine_status() -> dict:
    return engine.status()


@app.post("/api/engine/warmup")
async def engine_warmup(background_tasks: BackgroundTasks) -> dict:
    engine.touch()
    engine.mark_loading()

    async def warmup_once() -> None:
        async with warmup_lock:
            await asyncio.to_thread(engine.warmup, "large-v3-turbo")

    background_tasks.add_task(warmup_once)
    status = engine.status()
    if status["status"] == "standby":
        status["status"] = "loading"
        status["message"] = "Preparando motor de transcricao"
    return status


@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    language: str = Form(""),
    mode: str = Form("balanced"),
    task: str = Form("transcribe"),
    prompt: str = Form(""),
    vad_filter: bool = Form(True),
    light_cleanup: bool = Form(True),
    deep_noise_cleanup: bool = Form(False),
    separate_voice: bool = Form(False),
) -> list[Job]:
    engine.touch()
    if mode not in {"fast", "balanced", "accurate"}:
        raise HTTPException(status_code=400, detail="Modo invalido.")
    if task not in {"transcribe", "translate"}:
        raise HTTPException(status_code=400, detail="Tarefa invalida.")
    if language not in {"", "pt", "en", "es", "fr"}:
        raise HTTPException(status_code=400, detail="Idioma invalido.")
    if not files:
        raise HTTPException(status_code=400, detail="Envie pelo menos um arquivo.")

    created: list[Job] = []
    for file in files:
        job_id = uuid.uuid4().hex
        suffix = Path(file.filename or "media").suffix or ".bin"
        path = job_dir(job_id)
        media_path = path / f"original{suffix}"

        with media_path.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                out.write(chunk)

        job = Job(
            id=job_id,
            filename=file.filename or media_path.name,
            settings=JobSettings(
                language=language or None,
                mode=mode,
                task=task,
                prompt=prompt or None,
                vad_filter=vad_filter,
                light_cleanup=light_cleanup,
                deep_noise_cleanup=deep_noise_cleanup,
                separate_voice=separate_voice,
            ),
        )
        save_job(job)
        created.append(job)
        background_tasks.add_task(run_job, job_id, media_path)

    return created


@app.get("/api/jobs")
def list_jobs() -> list[Job]:
    if not jobs:
        load_jobs()
    return sorted(
        (job for job in jobs.values() if not job.hidden_from_tasks),
        key=lambda item: item.created_at,
        reverse=True,
    )


@app.get("/api/history/transcriptions")
def transcription_history() -> list[Job]:
    if not jobs:
        load_jobs()
    return sorted(
        (job for job in jobs.values() if job.status == JobStatus.done),
        key=lambda item: item.created_at,
        reverse=True,
    )


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> Job:
    job = jobs.get(job_id)
    path = job_dir(job_id) / "job.json"
    if job is None and path.exists():
        job = Job.model_validate_json(path.read_text(encoding="utf-8"))
        jobs[job.id] = job
    if job is None:
        raise HTTPException(status_code=404, detail="Transcricao nao encontrada.")
    return job


@app.post("/api/jobs/{job_id}/retry")
async def retry_job(job_id: str, background_tasks: BackgroundTasks) -> Job:
    engine.touch()
    job = get_job(job_id)
    if job.status in {JobStatus.queued, JobStatus.preparing, JobStatus.processing}:
        raise HTTPException(status_code=409, detail="Este job ja esta em andamento.")

    media_path = retry_source(job_id)
    for generated in (job_dir(job_id) / "audio.mp3", job_dir(job_id) / "transcription.wav"):
        if generated.exists() and generated.resolve() != media_path.resolve():
            generated.unlink(missing_ok=True)
    job.status = JobStatus.queued
    job.progress = 0.0
    job.message = "Na fila"
    job.error = None
    job.text = ""
    job.segments = []
    job.duration = None
    job.detected_language = None
    job.hidden_from_tasks = False
    job.cancel_requested = False
    save_job(job)
    background_tasks.add_task(run_job, job_id, media_path)
    return job


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> Job:
    job = get_job(job_id)
    if job.status not in {JobStatus.queued, JobStatus.preparing, JobStatus.processing}:
        return job
    job.cancel_requested = True
    job.message = "Cancelando"
    if job.status == JobStatus.queued:
        job.status = JobStatus.cancelled
        job.message = "Cancelado"
    save_job(job)
    return job


@app.post("/api/jobs/clear")
async def clear_jobs_list() -> dict:
    changed = 0
    for job in jobs.values():
        if job.status in {JobStatus.done, JobStatus.failed, JobStatus.cancelled} and not job.hidden_from_tasks:
            job.hidden_from_tasks = True
            save_job(job)
            changed += 1
    return {"ok": True, "hidden": changed}


@app.get("/api/jobs/{job_id}/audio")
def get_audio(job_id: str) -> FileResponse:
    job = get_job(job_id)
    audio_path = job_dir(job_id) / (job.audio_filename or "audio.mp3")
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio nao encontrado.")
    return FileResponse(audio_path, media_type="audio/mpeg", filename=audio_path.name)


@app.get("/api/jobs/{job_id}/export/srt")
def export_job_srt(job_id: str) -> Response:
    job = get_job(job_id)
    if job.status != JobStatus.done:
        raise HTTPException(status_code=409, detail="A transcricao ainda nao foi concluida.")
    if not job.segments:
        raise HTTPException(status_code=404, detail="Esta transcricao nao possui trechos com timestamps.")

    filename = srt_filename(job.filename)
    content = export_srt(job.segments)
    if not content.strip():
        raise HTTPException(status_code=404, detail="Nao ha texto suficiente para gerar SRT.")

    return Response(
        content=content.encode("utf-8"),
        media_type="application/x-subrip; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "Cache-Control": "no-store",
        },
    )


@app.post("/api/silence")
async def create_silence_tasks(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    profile: str = Form("normal"),
    strategy: str = Form("inteligente"),
    preserve_edges: bool = Form(True),
    separate_voice: bool = Form(False),
    threshold_db: int = Form(-38),
    min_silence_ms: int = Form(650),
    keep_silence_ms: int = Form(120),
) -> list[SilenceTask]:
    if not files:
        raise HTTPException(status_code=400, detail="Envie pelo menos um audio ou video.")
    if profile not in {"suave", "normal", "agressivo"}:
        raise HTTPException(status_code=400, detail="Perfil invalido.")
    if strategy not in {"inteligente", "voz_protegida", "volume_agressivo"}:
        raise HTTPException(status_code=400, detail="Estrategia invalida.")
    threshold_db = max(-80, min(-10, threshold_db))
    min_silence_ms = max(100, min(5000, min_silence_ms))
    keep_silence_ms = max(0, min(2000, keep_silence_ms))

    created: list[SilenceTask] = []
    for file in files:
        task_id = uuid.uuid4().hex
        suffix = Path(file.filename or "audio").suffix or ".bin"
        path = silence_dir(task_id)
        media_path = path / f"input{suffix}"

        with media_path.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                out.write(chunk)

        task = SilenceTask(
            id=task_id,
            filename=file.filename or media_path.name,
            settings=SilenceSettings(
                threshold_db=threshold_db,
                min_silence_ms=min_silence_ms,
                keep_silence_ms=keep_silence_ms,
                profile=profile,
                strategy=strategy,
                preserve_edges=preserve_edges,
                separate_voice=separate_voice,
            ),
            input_filename=media_path.name,
        )
        save_silence_task(task)
        created.append(task)
        background_tasks.add_task(run_silence_task, task_id, media_path)

    return created


@app.get("/api/silence/tasks")
def list_silence_tasks() -> list[SilenceTask]:
    if not silence_tasks:
        load_silence_tasks()
    return sorted(
        (task for task in silence_tasks.values() if not task.hidden_from_tasks),
        key=lambda item: item.created_at,
        reverse=True,
    )


@app.get("/api/silence/history")
def silence_history() -> list[SilenceTask]:
    if not silence_tasks:
        load_silence_tasks()
    return sorted(
        (task for task in silence_tasks.values() if task.status == JobStatus.done),
        key=lambda item: item.created_at,
        reverse=True,
    )


@app.get("/api/silence/{task_id}")
def get_silence_task(task_id: str) -> SilenceTask:
    task = silence_tasks.get(task_id)
    path = silence_dir(task_id) / "task.json"
    if task is None and path.exists():
        task = SilenceTask.model_validate_json(path.read_text(encoding="utf-8"))
        silence_tasks[task.id] = task
    if task is None:
        raise HTTPException(status_code=404, detail="Tarefa nao encontrada.")
    return task


@app.post("/api/silence/{task_id}/cancel")
async def cancel_silence_task(task_id: str) -> SilenceTask:
    task = get_silence_task(task_id)
    if task.status not in {JobStatus.queued, JobStatus.preparing, JobStatus.processing}:
        return task
    task.cancel_requested = True
    task.message = "Cancelando"
    if task.status == JobStatus.queued:
        task.status = JobStatus.cancelled
        task.message = "Cancelado"
    save_silence_task(task)
    return task


@app.post("/api/silence/{task_id}/retry")
async def retry_silence_task(task_id: str, background_tasks: BackgroundTasks) -> SilenceTask:
    task = get_silence_task(task_id)
    if task.status in {JobStatus.queued, JobStatus.preparing, JobStatus.processing}:
        raise HTTPException(status_code=409, detail="Esta tarefa ja esta em andamento.")
    media_path = silence_source(task_id)
    task.status = JobStatus.queued
    task.progress = 0.0
    task.message = "Na fila"
    task.error = None
    task.output_filename = None
    task.audio_url = None
    task.duration_output = None
    task.removed_seconds = None
    task.removed_percent = None
    task.engine = None
    task.kept_segments = 0
    task.silence_cuts = 0
    task.threshold_db_used = None
    task.hidden_from_tasks = False
    task.cancel_requested = False
    save_silence_task(task)
    background_tasks.add_task(run_silence_task, task_id, media_path)
    return task


@app.post("/api/silence/clear")
async def clear_silence_list() -> dict:
    changed = 0
    for task in silence_tasks.values():
        if task.status in {JobStatus.done, JobStatus.failed, JobStatus.cancelled} and not task.hidden_from_tasks:
            task.hidden_from_tasks = True
            save_silence_task(task)
            changed += 1
    return {"ok": True, "hidden": changed}


@app.get("/api/silence/{task_id}/audio")
def get_silence_audio(task_id: str) -> FileResponse:
    task = get_silence_task(task_id)
    audio_path = silence_dir(task_id) / (task.output_filename or "sem-silencio.mp3")
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio processado nao encontrado.")
    return FileResponse(audio_path, media_type="audio/mpeg", filename=audio_path.name)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/", StaticFiles(directory=STATIC), name="static")
