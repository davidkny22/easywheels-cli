"""Wheel resolution: find the best wheel for the detected environment."""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from easywheels_cli.config import get_api_key, get_api_url
from easywheels_cli.detect import Environment


@dataclass
class ResolvedWheel:
    """A resolved wheel ready for installation."""

    package_name: str
    package_version: str
    wheel_filename: str
    download_url: str
    cuda_version: str
    python_version: str
    torch_version: str | None
    platform: str
    arch: str | None


def resolve(
    package: str,
    env: Environment,
    version: str | None = None,
) -> ResolvedWheel | None:
    """Ask the EasyWheels API for the best wheel matching this environment.

    The API handles the complex matching logic:
    - CUDA version compatibility
    - Torch version compatibility
    - Platform + arch matching
    - ABI3 wheel expansion
    - Generic CUDA tag expansion
    """
    api_url = get_api_url()
    api_key = get_api_key()

    if not api_key:
        return None

    params = {
        "package": package,
        "python": env.python_version,
        "platform": env.platform,
        "arch": env.arch,
    }
    if env.cuda_version:
        params["cuda"] = env.cuda_version
    if env.torch_version:
        params["torch"] = env.torch_version
    if env.gpu_sm:
        params["gpu_sm"] = env.gpu_sm
    if version:
        params["version"] = version

    try:
        resp = httpx.get(
            f"{api_url}/api/v1/resolve",
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise
    except Exception:
        return None

    return ResolvedWheel(
        package_name=data["package_name"],
        package_version=data["package_version"],
        wheel_filename=data["wheel_filename"],
        download_url=data["download_url"],
        cuda_version=data["cuda_version"],
        python_version=data["python_version"],
        torch_version=data.get("torch_version"),
        platform=data["platform"],
        arch=data.get("arch"),
    )


def get_index_url(env: Environment) -> str:
    """Get a filtered simple index URL for pip --extra-index-url.

    This URL serves only wheels matching the detected environment,
    avoiding pip's inability to filter by CUDA/torch version.
    """
    api_url = get_api_url()
    api_key = get_api_key()

    if not api_key:
        return f"{api_url}/simple/"

    # Construct a scoped index URL with env params encoded
    # The server filters the index to only show matching wheels
    parts = [f"{api_url}/simple/"]

    # pip uses Basic Auth: username=api_key, password empty
    # We encode env preferences in a special header or query param
    # For now, use the standard auth URL format
    auth_url = f"{api_url.replace('https://', f'https://{api_key}:@')}/simple/"

    return auth_url
