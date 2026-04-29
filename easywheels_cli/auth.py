"""Authentication for EasyWheels CLI.

Two login methods:
1. GitHub device flow (opens browser, no password needed)
2. Email/password (entered in terminal)
"""
from __future__ import annotations

import getpass
import time
import webbrowser

import httpx
from rich.console import Console

from easywheels_cli.config import get_api_url, set_api_key

console = Console()

_GITHUB_CLIENT_ID = "Ov23liLhNRVPJ522X2UX"
_GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"


def login() -> str | None:
    """Interactive login. Returns the API key on success."""
    console.print("\n[bold]Log in to EasyWheels[/bold]\n")
    console.print("  [1] GitHub (opens browser)")
    console.print("  [2] Email and password\n")

    choice = input("  Choose [1/2]: ").strip()

    if choice == "2":
        return _email_login()
    return _github_login()


def _email_login() -> str | None:
    """Log in with email and password."""
    api_url = get_api_url()

    console.print()
    email = input("  Email: ").strip()
    if not email:
        console.print("[red]Email is required.[/red]")
        return None

    password = getpass.getpass("  Password: ")
    if not password:
        console.print("[red]Password is required.[/red]")
        return None

    console.print("\n  [dim]Logging in...[/dim]")

    try:
        resp = httpx.post(
            f"{api_url}/api/v1/auth/login/cli",
            json={"email": email, "password": password},
            timeout=15,
        )
    except Exception as e:
        console.print(f"\n  [red]Connection failed: {e}[/red]")
        return None

    if resp.status_code == 401:
        detail = resp.json().get("detail", "Invalid email or password")
        console.print(f"\n  [red]{detail}[/red]")
        return None

    if not resp.is_success:
        console.print(f"\n  [red]Login failed ({resp.status_code})[/red]")
        return None

    result = resp.json()
    api_key = result["api_key"]
    username = result.get("username", email)

    set_api_key(api_key)
    console.print(f"\n  [green bold]Logged in as {username}[/green bold]")
    console.print("  API key saved to ~/.easywheels/config.toml\n")
    return api_key


def _github_login() -> str | None:
    """Log in via GitHub device flow."""
    api_url = get_api_url()

    console.print("\n  [dim]Requesting device code from GitHub...[/dim]\n")

    try:
        resp = httpx.post(
            _GITHUB_DEVICE_CODE_URL,
            data={
                "client_id": _GITHUB_CLIENT_ID,
                "scope": "read:user,user:email",
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        console.print(f"  [red]Failed to request device code from GitHub: {e}[/red]")
        return None

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    interval = data.get("interval", 5)
    expires_in = data.get("expires_in", 900)

    console.print(f"  Open:  [bold cyan]{verification_uri}[/bold cyan]")
    console.print(f"  Code:  [bold yellow]{user_code}[/bold yellow]\n")

    try:
        webbrowser.open(verification_uri)
        console.print("  [dim]Browser opened. Enter the code above, then authorize EasyWheels.[/dim]\n")
    except Exception:
        console.print("  [dim]Open the URL above in your browser and enter the code.[/dim]\n")

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

    console.print("  [dim]GitHub authorized. Connecting to EasyWheels...[/dim]")

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
