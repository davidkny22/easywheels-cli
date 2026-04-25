# easywheels

> Install GPU Python packages without the headache.

`easywheels` auto-detects your CUDA version, GPU architecture, PyTorch version, and Python version, then installs the exact right pre-built wheel. No more hunting through compatibility matrices or building from source for 2 hours.

## Install

```bash
pip install easywheels
```

## Quick Start

```bash
# Log in with your GitHub account
easywheels login

# Install any GPU package. That's it.
easywheels install flash-attn
```

`easywheels` detects your environment automatically:

```
               Detected Environment
+-------------------------------------------------+
| Python     | cp312                              |
| Platform   | linux (x86_64)                     |
| CUDA       | cu128                              |
| GPU        | NVIDIA RTX 4090                    |
| GPU SM     | sm_89                              |
| PyTorch    | 2.9                                |
| Torch CUDA | 12.8                               |
+-------------------------------------------------+

Resolving flash-attn...
  Found: flash_attn-2.8.3+cu128torch2.9-cp312-cp312-linux_x86_64.whl
  CUDA: cu128, Torch: 2.9

Running: pip install flash_attn-2.8.3+cu128torch2.9-cp312-cp312-linux_x86_64.whl
```

## Why?

Installing GPU-accelerated Python packages on CUDA is painful:

- `flash-attn` has **362 wheel variants** for a single version. pip picks randomly.
- Building from source takes **2+ hours** and requires MSVC, CUDA toolkit, and Ninja.
- Wheels are scattered across PyPI, GitHub Releases, and HuggingFace.
- Getting the wrong CUDA or torch version means silent failures or crashes.

`easywheels` solves this by maintaining a registry of 2,300+ pre-built wheels and a CLI that knows exactly which one you need.

## Commands

### `easywheels install <package>`

Detects your environment and installs the best matching wheel from the EasyWheels registry.

```bash
easywheels install flash-attn
easywheels install mamba-ssm causal-conv1d
easywheels install flash-attn==2.8.3    # pin a version
easywheels install flash-attn -U        # upgrade
```

### `easywheels detect`

Shows your detected environment without installing anything. Useful for debugging.

```bash
easywheels detect
```

### `easywheels login`

Authenticates via GitHub using device OAuth. Opens your browser, you enter a short code, done. Your API key is stored in `~/.easywheels/config.toml`.

```bash
easywheels login
```

### `easywheels search <package>`

Shows all available wheels for a package that match your environment.

```bash
easywheels search flash-attn
```

### `easywheels config`

Manage configuration directly.

```bash
easywheels config --show              # show current config
easywheels config --set-key ew_xxx    # set API key manually
easywheels config --set-url https://custom.url
```

## What's in the Registry?

2,300+ pre-built wheels across 13 packages:

| Package | Linux | Windows | CUDA | Python |
|---------|-------|---------|------|--------|
| flash-attn | x86_64, aarch64 | x86_64 | cu124-cu131 | 3.10-3.14 |
| xformers | x86_64 | x86_64 | cu126-cu130 | 3.9+ (ABI3) |
| mamba-ssm | x86_64, aarch64 | coming soon | cu118-cu130 | 3.10-3.13 |
| causal-conv1d | x86_64, aarch64 | x86_64 | cu124-cu129 | 3.11-3.13 |
| deepspeed | x86_64 | x86_64 | cu118-cu130 | 3.9-3.13 |
| exllamav2 | x86_64 | x86_64 | cu118-cu130 | 3.10-3.13 |
| llama-cpp-python | x86_64 | x86_64 | cu121-cu130 | 3.9-3.13 |
| sageattention | x86_64 | x86_64 | cu124-cu130 | 3.9+ (ABI3) |
| vllm | x86_64 | - | cu130 | 3.8+ (ABI3) |
| torchao | x86_64 | - | cu124-cu130 | 3.9+ (ABI3) |
| flash-attn-3 | x86_64 | x86_64 | cu126-cu130 | 3.9+ (ABI3) |
| gptqmodel | x86_64 | - | cu126-cu130 | 3.10-3.13 |
| flashinfer | x86_64 | - | cu128-cu129 | 3.9+ (ABI3) |

GPU architectures: Turing (sm_75) through Hopper (sm_90) with PTX forward compatibility. Blackwell (sm_120) support rolling out.

## How It Works

1. **Detection.** The CLI checks `nvidia-smi`, `nvcc`, and `torch` to determine your CUDA version, GPU compute capability, and PyTorch version.

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

The CLI is free and open source. The registry requires a subscription.

**Why?** Building and hosting GPU wheels is expensive. Each wheel takes 20-30 minutes of GPU compute time to build, and the matrix is massive: 13 packages × 5 CUDA versions × 4 Python versions × 2 platforms × multiple torch versions. We maintain 2,300+ wheels, rebuild them when new GPU architectures launch, and keep them in sync with upstream releases.

That infrastructure costs real money (GPU compute, storage, bandwidth, CDN), and someone has to do the work of patching packages for Windows, testing compatibility, and keeping everything up to date. A subscription keeps the registry running and growing.

| Plan | Price | What you get |
|------|-------|-------------|
| **Trial** | Free | 14 days, 3 downloads, 1 custom build |
| **Lite** | $9/mo | 10 downloads/mo, registry access |
| **Pro** | $19/mo | Unlimited downloads, 3 custom builds/mo |
| **Team** | $49/mo | Unlimited downloads, 10 custom builds/mo, 5 team seats |

[Sign up at easywheels.io](https://easywheels.io/signup)

## Requirements

- Python 3.9+
- pip
- NVIDIA GPU with CUDA drivers (for GPU packages)
- PyTorch (optional, improves detection accuracy)

## Links

- **Registry**: [easywheels.io](https://easywheels.io)
- **Packages**: [easywheels.io/packages](https://easywheels.io/packages)
- **Wheel Finder**: [easywheels.io/search](https://easywheels.io/search)

## License

MIT
