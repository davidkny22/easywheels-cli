"""Environment detection: CUDA, GPU, torch, Python."""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Environment:
    """Detected environment for wheel resolution."""

    python_version: str  # "cp312"
    platform: str  # "linux" or "windows"
    arch: str  # "x86_64" or "aarch64"
    cuda_version: str | None  # "cu128" or None
    cuda_version_raw: str | None  # "12.8" or None
    gpu_name: str | None  # "NVIDIA RTX 4090" or None
    gpu_sm: str | None  # "sm_89" or None
    torch_version: str | None  # "2.9" or None
    torch_cuda: str | None  # "12.8" or None


def detect_python() -> tuple[str, str, str]:
    """Return (cpython_tag, platform, arch)."""
    major, minor = sys.version_info[:2]
    tag = f"cp{major}{minor}"

    if sys.platform == "win32":
        plat = "windows"
    elif sys.platform == "darwin":
        plat = "macos"
    else:
        plat = "linux"

    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "aarch64"
    else:
        arch = machine

    return tag, plat, arch


def detect_cuda_nvidia_smi() -> tuple[str | None, str | None]:
    """Detect CUDA version from nvidia-smi. Returns (raw_version, cuda_tag)."""
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return None, None

    try:
        result = subprocess.run(
            [nvidia_smi, "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None, None
    except Exception:
        return None, None

    # nvidia-smi shows the max supported CUDA version, not installed toolkit
    # Better: check nvcc or torch.version.cuda
    try:
        result = subprocess.run(
            [nvidia_smi], capture_output=True, text=True, timeout=10,
        )
        m = re.search(r"CUDA Version:\s*(\d+\.\d+)", result.stdout)
        if m:
            raw = m.group(1)
            return raw, _raw_to_tag(raw)
    except Exception:
        pass

    return None, None


def detect_cuda_nvcc() -> tuple[str | None, str | None]:
    """Detect CUDA version from nvcc. Returns (raw_version, cuda_tag)."""
    nvcc = shutil.which("nvcc")
    if not nvcc:
        return None, None

    try:
        result = subprocess.run(
            [nvcc, "--version"], capture_output=True, text=True, timeout=10,
        )
        m = re.search(r"release (\d+\.\d+)", result.stdout)
        if m:
            raw = m.group(1)
            return raw, _raw_to_tag(raw)
    except Exception:
        pass

    return None, None


def _detect_cuda_from_env() -> tuple[str | None, str | None]:
    """Detect CUDA from CUDA_PATH or CUDA_HOME env vars.

    Common on HPC clusters and Windows installs where nvcc isn't on PATH.
    Looks for nvcc inside the env-specified directory, or parses the version
    from the path itself (e.g. /usr/local/cuda-12.8).
    """
    for var in ("CUDA_PATH", "CUDA_HOME"):
        cuda_dir = os.environ.get(var)
        if not cuda_dir:
            continue

        # Try nvcc at the expected location
        nvcc = os.path.join(cuda_dir, "bin", "nvcc")
        if os.path.isfile(nvcc) or os.path.isfile(nvcc + ".exe"):
            try:
                result = subprocess.run(
                    [nvcc, "--version"], capture_output=True, text=True, timeout=10,
                )
                m = re.search(r"release (\d+\.\d+)", result.stdout)
                if m:
                    raw = m.group(1)
                    return raw, _raw_to_tag(raw)
            except Exception:
                pass

        # Fallback: parse version from path (e.g. /usr/local/cuda-12.8)
        m = re.search(r"cuda[_-]?(\d+\.\d+)", cuda_dir, re.IGNORECASE)
        if m:
            raw = m.group(1)
            return raw, _raw_to_tag(raw)

    return None, None


def detect_gpu() -> tuple[str | None, str | None]:
    """Detect GPU name and SM compute capability. Returns (name, sm_tag)."""
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            major, minor = torch.cuda.get_device_capability(0)
            sm = f"sm_{major}{minor}"
            return name, sm
    except ImportError:
        pass

    # Fallback: nvidia-smi
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            result = subprocess.run(
                [nvidia_smi, "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                name = result.stdout.strip().split("\n")[0]
                return name, _infer_sm_from_name(name)
        except Exception:
            pass

    return None, None


def detect_torch() -> tuple[str | None, str | None]:
    """Detect torch version and its CUDA version. Returns (torch_ver, cuda_ver)."""
    try:
        import torch
        ver = torch.__version__
        # Strip +cuXXX suffix: "2.9.0+cu128" -> "2.9.0"
        base = ver.split("+")[0]

        cuda = torch.version.cuda  # "12.8" or None
        return base, cuda
    except ImportError:
        return None, None


def detect() -> Environment:
    """Run full environment detection."""
    py_tag, plat, arch = detect_python()

    # CUDA: prefer torch's report, fall back to nvcc, CUDA_PATH/CUDA_HOME, then nvidia-smi
    torch_ver, torch_cuda = detect_torch()

    if torch_cuda:
        cuda_raw = torch_cuda
        cuda_tag = _raw_to_tag(torch_cuda)
    else:
        cuda_raw, cuda_tag = detect_cuda_nvcc()
        if not cuda_tag:
            cuda_raw, cuda_tag = _detect_cuda_from_env()
        if not cuda_tag:
            cuda_raw, cuda_tag = detect_cuda_nvidia_smi()

    gpu_name, gpu_sm = detect_gpu()

    return Environment(
        python_version=py_tag,
        platform=plat,
        arch=arch,
        cuda_version=cuda_tag,
        cuda_version_raw=cuda_raw,
        gpu_name=gpu_name,
        gpu_sm=gpu_sm,
        torch_version=torch_ver,
        torch_cuda=torch_cuda,
    )


def _raw_to_tag(raw: str) -> str:
    """Convert "12.8" to "cu128"."""
    parts = raw.split(".")
    if len(parts) == 2:
        major, minor = parts
        return f"cu{major}{minor}"
    return f"cu{raw.replace('.', '')}"


# Best-effort SM inference from GPU name when torch isn't available
_SM_MAP = {
    "1650": "sm_75", "1660": "sm_75",
    "2060": "sm_75", "2070": "sm_75", "2080": "sm_75",
    "3050": "sm_86", "3060": "sm_86", "3070": "sm_86", "3080": "sm_86", "3090": "sm_86",
    "A10": "sm_86", "A16": "sm_86", "A2": "sm_86",
    "A30": "sm_80", "A40": "sm_86", "A100": "sm_80",
    "4060": "sm_89", "4070": "sm_89", "4080": "sm_89", "4090": "sm_89",
    "L4": "sm_89", "L40": "sm_89", "L40S": "sm_89",
    "T4": "sm_75",
    "H100": "sm_90", "H200": "sm_90", "H20": "sm_90",
    "B100": "sm_120", "B200": "sm_120",
    "5070": "sm_120", "5080": "sm_120", "5090": "sm_120",
    "GB200": "sm_120", "GB300": "sm_120",
}


def _infer_sm_from_name(name: str) -> str | None:
    for key, sm in _SM_MAP.items():
        if key in name:
            return sm
    return None
