# src/fetcher.py
from __future__ import annotations
import requests
from pathlib import Path
import sys

# Base raw URL for the modm-io cmsis-svd-stm32 repo
_BASE_URL = "https://raw.githubusercontent.com/modm-io/cmsis-svd-stm32/main"

# Map of chip family prefix → folder in the repo
_FAMILY_MAP = {
    "STM32F0": "stm32f0",
    "STM32F1": "stm32f1",
    "STM32F2": "stm32f2",
    "STM32F3": "stm32f3",
    "STM32F4": "stm32f4",
    "STM32F7": "stm32f7",
    "STM32G0": "stm32g0",
    "STM32G4": "stm32g4",
    "STM32H7": "stm32h7",
    "STM32L0": "stm32l0",
    "STM32L1": "stm32l1",
    "STM32L4": "stm32l4",
    "STM32L5": "stm32l5",
    "STM32U5": "stm32u5",
    "STM32WB": "stm32wb",
}


def _resolve_family(chip: str) -> tuple[str, str]:
    """Return (family_folder, chip_original) or raise ValueError."""
    chip_upper = chip.upper()
    for prefix, folder in _FAMILY_MAP.items():
        if chip_upper.startswith(prefix):
            return folder, chip
    raise ValueError(
        f"Unknown chip family for '{chip}'.\n"
        f"Supported prefixes: {', '.join(_FAMILY_MAP)}"
    )


def fetch_svd(chip: str, svd_dir: str | Path = "svd_files") -> Path:
    """
    Download an SVD file for the given chip name.
    Tries common suffix variants if exact name not found.

    Examples:
        fetch_svd("STM32F103")   → tries STM32F103.svd, STM32F103xx.svd, STM32F103x6.svd ...
        fetch_svd("STM32F0x0")   → svd_files/STM32F0x0.svd
    """
    svd_dir = Path(svd_dir)
    svd_dir.mkdir(parents=True, exist_ok=True)

    folder, chip_name = _resolve_family(chip)

    # Variants to try in order — exact name first, then common suffixes
    candidates = [
        chip_name,
        f"{chip_name}xx",
        f"{chip_name}x6",
        f"{chip_name}x8",
        f"{chip_name}xB",
        f"{chip_name}xC",
        f"{chip_name}xE",
        f"{chip_name}xG",
    ]

    for candidate in candidates:
        filename = f"{candidate}.svd"
        out_path = svd_dir / filename

        # Return immediately if already cached
        if out_path.exists():
            print(f"[fetch] Already cached: {out_path}")
            return out_path

        url = f"{_BASE_URL}/{folder}/{filename}"
        print(f"[fetch] Trying {url} ...")

        try:
            response = requests.get(url, timeout=15)
        except requests.RequestException as e:
            print(f"[fetch] Network error: {e}", file=sys.stderr)
            continue

        if response.status_code == 404:
            continue  # try next variant

        response.raise_for_status()

        content = response.text
        if not content.strip().startswith("<?xml"):
            continue  # not valid XML, try next

        out_path.write_text(content, encoding="utf-8")
        print(f"[fetch] Saved → {out_path}")
        return out_path

    raise FileNotFoundError(
        f"Could not find an SVD file for '{chip}' in folder '{folder}'.\n"
        f"Tried variants: {', '.join(candidates)}\n"
        f"Browse available files at: https://github.com/modm-io/cmsis-svd-stm32/tree/main/{folder}"
    )