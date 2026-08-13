from __future__ import annotations

import os
from pathlib import Path


def _candidate_dirs() -> list[Path]:
    root = Path(__file__).resolve().parent.parent
    venv = root / ".venv" / "Lib" / "site-packages"
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    cuda_root = program_files / "NVIDIA GPU Computing Toolkit" / "CUDA"

    candidates = [
        venv / "nvidia" / "cublas" / "bin",
        venv / "nvidia" / "cudnn" / "bin",
        venv / "nvidia" / "cuda_runtime" / "bin",
    ]
    for version in ("v12.6", "v12.5", "v12.4", "v12.3", "v12.2", "v12.1", "v12.0"):
        candidates.append(cuda_root / version / "bin")
    return candidates


def configure_cuda_dll_paths() -> list[str]:
    added: list[str] = []
    path_parts = os.environ.get("PATH", "").split(os.pathsep)
    for candidate in _candidate_dirs():
        if not candidate.exists():
            continue
        text = str(candidate)
        if text not in path_parts:
            path_parts.insert(0, text)
        try:
            os.add_dll_directory(text)
        except Exception:
            pass
        added.append(text)
    os.environ["PATH"] = os.pathsep.join(path_parts)
    return added


CUDA_DLL_PATHS = configure_cuda_dll_paths()
