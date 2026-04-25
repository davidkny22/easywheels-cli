"""Device OAuth flow for GitHub-based authentication.

Flow:
1. CLI requests a device code from our API
2. User opens browser to easywheels.io/device and enters the code
3. User authenticates via GitHub OAuth on our site
4. CLI polls our API until the device code is confirmed
5. API returns an API key tied to the user's account
"""
from __future__ import annotations

import time
import webbrowser

import httpx
from rich.console import Console

from easywheels_cli.config import get_api_url, set_api_key

console = Console()


def device_login() -> str | None:
    """Run the device OAuth flow. Returns the API key on success."""
    api_url = get_api_url()

    # Step 1: Request device code
    console.print("\n[bold]Logging in to EasyWheels...[/bold]\n")

    try:
        resp = httpx.post(f"{api_url}/api/v1/auth/device/code", timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        console.print(f"[red]Failed to request device code: {e}[/red]")
        return None

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_url = data["verification_url"]
    interval = data.get("interval", 5)
    expires_in = data.get("expires_in", 300)

    # Step 2: Show code and open browser
    console.print(f"  Open: [bold cyan]{verification_url}[/bold cyan]")
    console.print(f"  Enter code: [bold yellow]{user_code}[/bold yellow]\n")

    try:
        webbrowser.open(verification_url)
        console.print("  [dim]Browser opened. Waiting for authorization...[/dim]")
    except Exception:
        console.print("  [dim]Please open the URL above in your browser.[/dim]")

    # Step 3: Poll for completion
    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)

        try:
            resp = httpx.post(
                f"{api_url}/api/v1/auth/device/token",
                json={"device_code": device_code},
                timeout=10,
            )
        except Exception:
            continue

        if resp.status_code == 200:
            result = resp.json()
            api_key = result["api_key"]
            username = result.get("username", "")

            set_api_key(api_key)
            console.print(f"\n  [green bold]Logged in as {username}![/green bold]")
            console.print(f"  API key saved to ~/.easywheels/config.toml\n")
            return api_key

        if resp.status_code == 428:
            # Authorization pending — keep polling
            continue

        if resp.status_code == 410:
            console.print("\n  [red]Device code expired. Please try again.[/red]")
            return None

        if resp.status_code == 409:
            console.print("\n  [red]Device code already used.[/red]")
            return None

    console.print("\n  [red]Timed out waiting for authorization.[/red]")
    return None
