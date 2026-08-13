from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    preparing = "preparing"
    processing = "processing"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    speaker: Optional[str] = None


class JobSettings(BaseModel):
    language: Optional[str] = None
    mode: str = "balanced"
    task: str = "transcribe"
    prompt: Optional[str] = None
    vad_filter: bool = True
    light_cleanup: bool = True
    deep_noise_cleanup: bool = False
    separate_voice: bool = False


class Job(BaseModel):
    id: str
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: JobStatus = JobStatus.queued
    progress: float = 0.0
    message: str = "Na fila"
    settings: JobSettings
    duration: Optional[float] = None
    detected_language: Optional[str] = None
    audio_url: Optional[str] = None
    audio_filename: Optional[str] = None
    text: str = ""
    segments: list[Segment] = Field(default_factory=list)
    error: Optional[str] = None
    hidden_from_tasks: bool = False
    cancel_requested: bool = False


class SilenceSettings(BaseModel):
    threshold_db: int = -38
    min_silence_ms: int = 650
    keep_silence_ms: int = 120
    profile: str = "normal"
    strategy: str = "inteligente"
    preserve_edges: bool = True
    separate_voice: bool = False


class SilenceTask(BaseModel):
    id: str
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: JobStatus = JobStatus.queued
    progress: float = 0.0
    message: str = "Na fila"
    settings: SilenceSettings = Field(default_factory=SilenceSettings)
    input_filename: Optional[str] = None
    output_filename: Optional[str] = None
    audio_url: Optional[str] = None
    duration_original: Optional[float] = None
    duration_output: Optional[float] = None
    removed_seconds: Optional[float] = None
    removed_percent: Optional[float] = None
    engine: Optional[str] = None
    kept_segments: int = 0
    silence_cuts: int = 0
    threshold_db_used: Optional[float] = None
    error: Optional[str] = None
    hidden_from_tasks: bool = False
    cancel_requested: bool = False
