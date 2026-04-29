# easywheels

> Install GPU Python packages without the headache.

`easywheels` auto-detects your CUDA version, GPU architecture, PyTorch version, and Python version, then installs the exact right pre-built wheel. No more hunting through compatibility matrices or building from source.

## Install

```bash
pip install easywheels
```

## Quick Start

```bash
# Log in with your GitHub account
easywheels login

# Install any GPU package
easywheels install flash-attn
```

`easywheels` detects your environment automatically:

```
Detected: Python 3.12, CUDA 12.8, RTX 4090 (sm_89), torch 2.9.0

Resolving flash-attn...
  Found: flash_attn-2.8.3+cu128torch2.9-cp312-cp312-linux_x86_64.whl
  CUDA: cu128, Torch: 2.9

Running: pip install flash_attn-2.8.3+cu128torch2.9-cp312-cp312-linux_x86_64.whl
Done in 9 seconds.
```

## Why?

Installing GPU Python packages on CUDA is painful:

- Some packages ship source-only on PyPI. No pre-built wheels at all.
- Pre-built wheels that do exist are scattered across GitHub repos, custom indices, and community forks.
- Many CUDA/Python/platform combos simply don't have a wheel anywhere.
- Building from source takes 30-120 minutes and frequently fails.

`easywheels` solves this. It mirrors pre-built wheels from every upstream source and builds the gaps on GPU infrastructure. 2,200+ wheels across 10 packages, served through a single registry.

## Commands

### `easywheels install <package>`

Detects your environment and installs the best matching wheel.

```bash
easywheels install flash-attn
easywheels install mamba-ssm causal-conv1d
easywheels install flash-attn==2.8.3    # pin a version
easywheels install flash-attn -U        # upgrade
easywheels install flash-attn --dry-run # show what would install
```

### `easywheels detect`

Shows your detected environment without installing anything.

```bash
easywheels detect
```

### `easywheels login`

Authenticates via GitHub device OAuth. Opens your browser, you authorize, done. Your API key is stored in `~/.easywheels/config.toml`.

```bash
easywheels login
```

### `easywheels search <package>`

Shows all available wheels for a package that match your environment.

```bash
easywheels search flash-attn
```

### `easywheels config`

Manage configuration.

```bash
easywheels config --show
easywheels config --set-key ew_xxx
```

## What's in the Registry?

2,200+ pre-built wheels across 10 packages:

- flash-attn, flash-attn-3, deepspeed, mamba-ssm, causal-conv1d, exllamav2, llama-cpp-python, gptqmodel, sageattention, flashinfer-jit-cache
- CUDA 12.4 through 13.0
- Python 3.10-3.13
- Linux fully covered. Windows build-out in progress.

GPU architectures: Turing (sm_75) through Hopper (sm_90) with PTX forward compatibility.

## How It Works

1. **Detection.** The CLI checks `nvidia-smi`, `nvcc`, `CUDA_PATH`/`CUDA_HOME`, and `torch` to determine your CUDA version, GPU compute capability, and PyTorch version.

2. **Resolution.** Your environment is sent to the EasyWheels API, which finds the best compatible wheel considering CUDA version, torch ABI, platform, and architecture.

3. **Installation.** The exact right wheel is downloaded and handed to pip. No guessing, no source builds.

## Configuration

Config lives in `~/.easywheels/config.toml`:

```toml
api_key = "ew_abc123..."
api_url = "https://easywheels.io"
```

You can also set `EASYWHEELS_API_KEY` as an environment variable.

## Pricing

The CLI is free and open source. The registry requires a subscription because building and hosting GPU wheels costs real money.

| Plan | Price | Downloads |
|------|-------|-----------|
| **Trial** | Free 14 days | 3 downloads |
| **Lite** | $9/mo | 10/mo |
| **Pro** | $19/mo | Unlimited |
| **Team** | $49/mo | Unlimited, 5 seats |

[Sign up at easywheels.io](https://easywheels.io/signup)

## Requirements

- Python 3.9+
- pip
- NVIDIA GPU with CUDA drivers (for GPU packages)
- PyTorch (optional, improves detection accuracy)

## Links

- **Registry**: [easywheels.io](https://easywheels.io)
- **Packages**: [easywheels.io/packages](https://easywheels.io/packages)

## License

MIT
