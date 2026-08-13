from __future__ import annotations

import gc
import threading
import time
from typing import Callable, Iterable, Optional

from app.cuda_paths import CUDA_DLL_PATHS


CUDA_ERROR_MARKERS = (
    "cublas",
    "cudnn",
    "cuda",
    "cufft",
    "curand",
    "cusolver",
    "cusparse",
    "dll is not found",
    "cannot be loaded",
)


class EngineManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._inference_lock = threading.Lock()
        self._model = None
        self._model_size: Optional[str] = None
        self._device: Optional[str] = None
        self._compute_type: Optional[str] = None
        self._status = "standby"
        self._message = "Motor em stand-by"
        self._last_error: Optional[str] = None
        self._fallback_reason: Optional[str] = None
        self._last_activity = time.time()
        self.standby_after_seconds = 20 * 60

    def touch(self) -> None:
        self._last_activity = time.time()

    def status(self) -> dict:
        with self._lock:
            idle_seconds = max(0, int(time.time() - self._last_activity))
            return {
                "status": self._status,
                "message": self._message,
                "device": self._device,
                "compute_type": self._compute_type,
                "model_size": self._model_size,
                "last_error": self._last_error,
                "fallback_reason": self._fallback_reason,
                "idle_seconds": idle_seconds,
                "standby_after_seconds": self.standby_after_seconds,
                "cuda_dll_paths": CUDA_DLL_PATHS,
            }

    def mark_loading(self, message: str = "Preparando motor de transcricao") -> None:
        with self._lock:
            if self._model is None:
                self._status = "loading"
                self._message = message

    def warmup(self, model_size: str = "large-v3") -> dict:
        with self._lock:
            self.touch()
            if self._inference_lock.locked() and self._model is not None:
                self._status = "ready"
                self._message = f"Motor em uso em {self._device.upper()}"
                return self.status()
            if self._model is not None and self._model_size == model_size:
                self._status = "ready"
                self._message = f"Motor pronto em {self._device.upper()}"
                return self.status()

            self._status = "loading"
            self._message = "Verificando GPU e carregando modelo"
            self._last_error = None
            self._fallback_reason = None

            if self._has_cuda():
                try:
                    self._load_model(model_size, "cuda", "float16")
                    self._message = "Motor pronto em GPU CUDA"
                    return self.status()
                except Exception as exc:
                    if not self._is_cuda_error(exc):
                        self._status = "failed"
                        self._last_error = str(exc)
                        self._message = "Falha ao carregar motor"
                        raise
                    self._fallback_reason = str(exc)
                    self._last_error = str(exc)
                    self._unload_locked()

            self._load_model(model_size, "cpu", "int8")
            if self._fallback_reason:
                self._message = "GPU indisponivel, usando CPU"
            else:
                self._message = "Motor pronto em CPU"
            return self.status()

    def transcribe_audio(
        self,
        audio_path: str,
        *,
        model_size: str,
        language: Optional[str],
        task: str,
        beam_size: int,
        vad_filter: bool,
        initial_prompt: Optional[str],
        progress: Callable[[int, object], None],
        reset: Optional[Callable[[], None]] = None,
    ) -> tuple[list[object], object]:
        self.warmup(model_size)

        try:
            return self._transcribe_with_current_model(
                audio_path,
                language=language,
                task=task,
                beam_size=beam_size,
                vad_filter=vad_filter,
                initial_prompt=initial_prompt,
                progress=progress,
            )
        except Exception as exc:
            if self._device != "cuda" or not self._is_cuda_error(exc):
                raise

            with self._lock:
                self._fallback_reason = str(exc)
                self._last_error = str(exc)
                self._status = "loading"
                self._message = "GPU falhou durante a transcricao, alternando para CPU"
                self._unload_locked()
                self._load_model(model_size, "cpu", "int8")
                self._message = "GPU indisponivel, usando CPU"

            if reset:
                reset()

            return self._transcribe_with_current_model(
                audio_path,
                language=language,
                task=task,
                beam_size=beam_size,
                vad_filter=vad_filter,
                initial_prompt=initial_prompt,
                progress=progress,
            )

    def maybe_standby(self, active_jobs: bool) -> None:
        with self._lock:
            if active_jobs or self._model is None:
                return
            if time.time() - self._last_activity < self.standby_after_seconds:
                return
            self._unload_locked()
            self._status = "standby"
            self._message = "Motor em stand-by para economizar recursos"

    def unload(self) -> None:
        with self._lock:
            self._unload_locked()
            self._status = "standby"
            self._message = "Motor em stand-by"

    def _transcribe_with_current_model(
        self,
        audio_path: str,
        *,
        language: Optional[str],
        task: str,
        beam_size: int,
        vad_filter: bool,
        initial_prompt: Optional[str],
        progress: Callable[[int, object], None],
    ) -> tuple[list[object], object]:
        with self._inference_lock:
            with self._lock:
                model = self._model
                if model is None:
                    raise RuntimeError("Motor de transcricao nao esta carregado.")
                self.touch()
                self._status = "ready"

            segments_iter, info = model.transcribe(
                audio_path,
                language=language,
                task=task,
                beam_size=beam_size,
                vad_filter=vad_filter,
                initial_prompt=initial_prompt,
            )

            segments = []
            for index, segment in enumerate(segments_iter, start=1):
                self.touch()
                segments.append(segment)
                progress(index, segment)

            return segments, info

    def _load_model(self, model_size: str, device: str, compute_type: str) -> None:
        from faster_whisper import WhisperModel

        self._unload_locked()
        self._status = "loading"
        self._message = f"Carregando modelo {model_size} em {device.upper()}"
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._status = "ready"
        self._last_error = None

    def _unload_locked(self) -> None:
        self._model = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _has_cuda(self) -> bool:
        try:
            import ctranslate2

            return ctranslate2.get_cuda_device_count() > 0
        except Exception:
            return False

    def _is_cuda_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return any(marker in message for marker in CUDA_ERROR_MARKERS)


engine = EngineManager()
