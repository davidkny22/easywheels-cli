# EasyWheels CLI

Smart GPU wheel installer — auto-detects CUDA, GPU, torch, and Python to install the right wheel.

## Install

```bash
pip install easywheels
```

## Usage

```bash
# Login (device OAuth via GitHub)
easywheels login

# Auto-detect environment and install the right wheel
easywheels install flash-attn

# Show detected environment
easywheels detect

# Search available wheels
easywheels search flash-attn
```
