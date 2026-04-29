"""GitHub Device Flow authentication for EasyWheels CLI.

Flow:
1. CLI requests a device code from GitHub directly
2. User opens github.com/login/device and enters the code
3. CLI polls GitHub until the user authorizes
4. CLI sends the GitHub access token to our API
5. API returns an EasyWheels API key
"""
from __future__ import annotations

import time
import webbrowser

import httpx
from rich.console import Console

from easywheels_cli.config import get_api_url, set_api_key

console = Console()

_GITHUB_CLIENT_ID = "Ov23liBlMVOxGkOXWX2q"
_GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_DEVICE_URL = "https://github.com/login/device"


def device_login() -> str | None:
    """Run GitHub Device Flow login. Returns the API key on success."""
    api_url = get_api_url()

    console.print("\n[bold]Logging in to EasyWheels via GitHub...[/bold]\n")

    # Step 1: Request device code from GitHub
    try:
        resp = httpx.post(
            _GITHUB_DEVICE_CODE_URL,
            data={
                "client_id": _GITHUB_CLIENT_ID,
                "scope": "read:user user:email",
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        console.print(f"[red]Failed to request device code from GitHub: {e}[/red]")
        return None

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    interval = data.get("interval", 5)
    expires_in = data.get("expires_in", 900)

    # Step 2: Show code and open browser
    console.print(f"  Open:  [bold cyan]{verification_uri}[/bold cyan]")
    console.print(f"  Code:  [bold yellow]{user_code}[/bold yellow]\n")

    try:
        webbrowser.open(verification_uri)
        console.print("  [dim]Browser opened. Enter the code above, then authorize EasyWheels.[/dim]\n")
    except Exception:
        console.print("  [dim]Open the URL above in your browser and enter the code.[/dim]\n")

    # Step 3: Poll GitHub for access token
    console.print("  [dim]Waiting for authorization...[/dim]")
    deadline = time.time() + expires_in
    github_token = None

    while time.time() < deadline:
        time.sleep(interval)

        try:
            resp = httpx.post(
                _GITHUB_TOKEN_URL,
                data={
                    "client_id": _GITHUB_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            token_data = resp.json()
        except Exception:
            continue

        error = token_data.get("error")

        if error == "authorization_pending":
            continue

        if error == "slow_down":
            interval = token_data.get("interval", interval + 5)
            continue

        if error == "expired_token":
            console.print("\n  [red]Device code expired. Please try again.[/red]")
            return None

        if error == "access_denied":
            console.print("\n  [red]Authorization denied.[/red]")
            return None

        if error:
            console.print(f"\n  [red]GitHub error: {error}[/red]")
            return None

        github_token = token_data.get("access_token")
        if github_token:
            break

    if not github_token:
        console.print("\n  [red]Timed out waiting for authorization.[/red]")
        return None

    # Step 4: Exchange GitHub token for EasyWheels API key
    console.print("  [dim]GitHub authorized. Creating EasyWheels account...[/dim]")

    try:
        resp = httpx.post(
            f"{api_url}/api/v1/auth/github/token",
            json={"access_token": github_token},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        console.print(f"\n  [red]Failed to exchange token: {e}[/red]")
        return None

    api_key = result["api_key"]
    username = result.get("username", "")

    set_api_key(api_key)
    console.print(f"\n  [green bold]Logged in as {username}[/green bold]")
    console.print("  API key saved to ~/.easywheels/config.toml\n")
    return api_key
