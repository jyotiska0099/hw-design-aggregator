# src/fetcher.py
from __future__ import annotations
import requests
from pathlib import Path

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

    Examples:
        fetch_svd("STM32F0x0")   → svd_files/STM32F0x0.svd
        fetch_svd("STM32F103xx") → svd_files/STM32F103xx.svd
    """
    svd_dir = Path(svd_dir)
    svd_dir.mkdir(parents=True, exist_ok=True)

    folder, chip_upper = _resolve_family(chip)
    filename = f"{chip_upper}.svd"
    out_path = svd_dir / filename

    if out_path.exists():
        print(f"[fetch] Already cached: {out_path}")
        return out_path

    url = f"{_BASE_URL}/{folder}/{filename}"
    print(f"[fetch] Downloading {url} ...")

    response = requests.get(url, timeout=15)

    if response.status_code == 404:
        raise FileNotFoundError(
            f"SVD not found for '{chip}' at {url}\n"
            f"Check available files at: https://github.com/modm-io/cmsis-svd-stm32/tree/main/{folder}"
        )

    response.raise_for_status()

    # Sanity check — make sure we got XML not an HTML error page
    content = response.text
    if not content.strip().startswith("<?xml"):
        raise ValueError(
            f"Downloaded content doesn't look like XML.\n"
            f"Got: {content[:120]}"
        )

    out_path.write_text(content, encoding="utf-8")
    print(f"[fetch] Saved → {out_path}")
    return out_path