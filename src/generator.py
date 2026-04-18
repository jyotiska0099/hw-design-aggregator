# src/generator.py
from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.models import Device


def _total_registers(peripherals) -> int:
    return sum(len(p.registers) for p in peripherals)

def _bit_mask(bit_width: int, bit_offset: int) -> str:
    """Compute register field bitmask as uppercase hex string."""
    mask = (2 ** bit_width - 1) << bit_offset
    return format(mask, "X")


def _jinja_env(template_dir: str | Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["bit_mask"] = _bit_mask
    env.filters["total_registers"] = _total_registers
    return env


def generate_header(device: Device,
                    template_dir: str | Path = "templates",
                    output_dir: str | Path = "output/headers") -> Path:
    env = _jinja_env(template_dir)
    template = env.get_template("header.h.j2")
    rendered = template.render(device=device)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{device.name}.h"
    out_path.write_text(rendered)
    return out_path


def generate_report(device: Device,
                    template_dir: str | Path = "templates",
                    output_dir: str | Path = "output/reports") -> Path:
    env = _jinja_env(template_dir)
    template = env.get_template("report.md.j2")
    rendered = template.render(device=device)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{device.name}.md"
    out_path.write_text(rendered)
    return out_path