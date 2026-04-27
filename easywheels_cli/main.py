"""EasyWheels CLI — smart GPU wheel installer.

Usage:
    easywheels install flash-attn
    easywheels detect
    easywheels login
    easywheels search flash-attn
"""
from __future__ import annotations

import subprocess
import sys

from rich.console import Console
from rich.table import Table

from easywheels_cli import __version__
from easywheels_cli.config import get_api_key, get_api_url
from easywheels_cli.detect import Environment, detect

console = Console()


def _print_env(env: Environment) -> None:
    """Pretty-print detected environment."""
    table = Table(title="Detected Environment", show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Python", env.python_version)
    table.add_row("Platform", f"{env.platform} ({env.arch})")
    table.add_row("CUDA", env.cuda_version or "[red]not detected[/red]")
    if env.cuda_version_raw:
        table.add_row("CUDA (raw)", env.cuda_version_raw)
    table.add_row("GPU", env.gpu_name or "[red]not detected[/red]")
    if env.gpu_sm:
        table.add_row("GPU SM", env.gpu_sm)
    table.add_row("PyTorch", env.torch_version or "[dim]not installed[/dim]")
    if env.torch_cuda:
        table.add_row("Torch CUDA", env.torch_cuda)

    console.print(table)


def cmd_detect() -> None:
    """Detect and display the current environment."""
    env = detect()
    _print_env(env)

    if not env.cuda_version:
        console.print("\n[yellow]No CUDA detected. GPU packages require CUDA.[/yellow]")
    if not env.torch_version:
        console.print("[dim]Install PyTorch first for best wheel matching.[/dim]")


def cmd_login() -> None:
    """Authenticate via device OAuth flow."""
    from easywheels_cli.auth import device_login
    device_login()


def cmd_install(packages: list[str], pip_args: list[str]) -> None:
    """Install packages with auto-detected environment."""
    api_key = get_api_key()
    if not api_key:
        console.print("[yellow]Not logged in. Run:[/yellow] easywheels login")
        console.print("[dim]Or set EASYWHEELS_API_KEY environment variable.[/dim]\n")
        return

    env = detect()
    console.print()
    _print_env(env)
    console.print()

    if not env.cuda_version:
        console.print("[yellow]No CUDA detected — installing CPU-only versions.[/yellow]\n")

    from easywheels_cli.resolve import resolve

    for package in packages:
        # Parse package==version if specified
        pkg_name = package
        pkg_version = None
        if "==" in package:
            pkg_name, pkg_version = package.split("==", 1)

        console.print(f"[bold]Resolving {pkg_name}...[/bold]")

        wheel = resolve(pkg_name, env, version=pkg_version)

        if wheel:
            console.print(f"  Found: [green]{wheel.wheel_filename}[/green]")
            console.print(f"  CUDA: {wheel.cuda_version}, Torch: {wheel.torch_version or 'any'}")
            console.print()

            # Install via pip — embed auth in URL for the simple index download
            auth_url = wheel.download_url.replace("https://", f"https://{api_key}:@")
            cmd = [
                sys.executable, "-m", "pip", "install",
                auth_url,
                "--no-deps",
                *pip_args,
            ]
            console.print(f"[dim]Running: pip install {wheel.wheel_filename}[/dim]\n")
            result = subprocess.run(cmd)
            if result.returncode != 0:
                console.print(f"[red]Failed to install {pkg_name}[/red]")
        else:
            # Fallback: use the index URL with pip
            console.print(f"  [dim]No exact match from API, falling back to index...[/dim]")
            api_url = get_api_url()
            index_url = f"{api_url.replace('https://', f'https://{api_key}:@')}/simple/"

            cmd = [
                sys.executable, "-m", "pip", "install",
                package,
                "--extra-index-url", index_url,
                "--prefer-binary",
                *pip_args,
            ]
            console.print(f"[dim]Running: pip install {package} --extra-index-url easywheels.io/simple/[/dim]\n")
            result = subprocess.run(cmd)
            if result.returncode != 0:
                console.print(f"[red]Failed to install {pkg_name}[/red]")


def cmd_search(package: str) -> None:
    """Search for available wheels for a package."""
    import httpx
    from easywheels_cli.config import get_api_key, get_api_url

    api_key = get_api_key()
    api_url = get_api_url()
    env = detect()

    console.print(f"\n[bold]Searching for {package}...[/bold]\n")

    try:
        resp = httpx.get(
            f"{api_url}/api/v1/resolve/search",
            params={
                "package": package,
                "python": env.python_version,
                "platform": env.platform,
                "cuda": env.cuda_version or "",
                "torch": env.torch_version or "",
            },
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json()
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        return

    if not results.get("wheels"):
        console.print(f"[yellow]No wheels found for {package}[/yellow]")
        return

    table = Table(title=f"Available wheels for {package}")
    table.add_column("Version")
    table.add_column("CUDA")
    table.add_column("Torch")
    table.add_column("Python")
    table.add_column("Platform")

    for w in results["wheels"]:
        table.add_row(
            w["version"],
            w["cuda_version"],
            w.get("torch_version", "-"),
            w["python_version"],
            w["platform"],
        )

    console.print(table)


def app() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="easywheels",
        description="Smart GPU wheel installer — auto-detects CUDA, GPU, torch, and Python.",
    )
    parser.add_argument("--version", action="version", version=f"easywheels {__version__}")

    sub = parser.add_subparsers(dest="command")

    # install
    install_p = sub.add_parser("install", aliases=["i"], help="Install GPU packages")
    install_p.add_argument("packages", nargs="+", help="Packages to install")
    install_p.add_argument("--no-deps", action="store_true", help="Don't install dependencies")
    install_p.add_argument("--force-reinstall", action="store_true")
    install_p.add_argument("--upgrade", "-U", action="store_true")

    # detect
    sub.add_parser("detect", aliases=["env"], help="Show detected environment")

    # login
    sub.add_parser("login", help="Authenticate with EasyWheels")

    # search
    search_p = sub.add_parser("search", aliases=["s"], help="Search available wheels")
    search_p.add_argument("package", help="Package name to search")

    # config
    config_p = sub.add_parser("config", help="Manage configuration")
    config_p.add_argument("--set-url", help="Set API URL")
    config_p.add_argument("--set-key", help="Set API key directly")
    config_p.add_argument("--show", action="store_true", help="Show current config")

    args = parser.parse_args()

    if args.command in ("detect", "env"):
        cmd_detect()
    elif args.command == "login":
        cmd_login()
    elif args.command in ("install", "i"):
        pip_args = []
        if getattr(args, "no_deps", False):
            pip_args.append("--no-deps")
        if getattr(args, "force_reinstall", False):
            pip_args.append("--force-reinstall")
        if getattr(args, "upgrade", False):
            pip_args.append("--upgrade")
        cmd_install(args.packages, pip_args)
    elif args.command in ("search", "s"):
        cmd_search(args.package)
    elif args.command == "config":
        from easywheels_cli.config import load_config, set_api_key, set_api_url
        if args.set_url:
            set_api_url(args.set_url)
            console.print(f"API URL set to: {args.set_url}")
        if args.set_key:
            set_api_key(args.set_key)
            console.print("API key saved.")
        if args.show:
            cfg = load_config()
            for k, v in cfg.items():
                if k == "api_key":
                    console.print(f"  {k}: {v[:8]}...")
                else:
                    console.print(f"  {k}: {v}")
    else:
        parser.print_help()
