# main.py
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from src.parser import parse_svd
from src.generator import generate_header, generate_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hw-aggregator",
        description="Hardware Design Data Aggregator — parse SVD files, generate C headers & Markdown reports.",
    )
    p.add_argument(
        "--svd",
        required=True,
        metavar="FILE",
        help="Path to the .svd input file",
    )
    p.add_argument(
        "--output",
        choices=["header", "report", "both"],
        default="both",
        help="What to generate (default: both)",
    )
    p.add_argument(
        "--out-dir",
        default="output",
        metavar="DIR",
        help="Root output directory (default: output/)",
    )
    p.add_argument(
        "--templates",
        default="templates",
        metavar="DIR",
        help="Jinja2 templates directory (default: templates/)",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()

    svd_path = Path(args.svd)
    if not svd_path.exists():
        print(f"[ERROR] SVD file not found: {svd_path}", file=sys.stderr)
        return 1

    print(f"[1/3] Parsing  {svd_path} ...")
    try:
        device = parse_svd(svd_path)
    except Exception as e:
        print(f"[ERROR] Failed to parse SVD: {e}", file=sys.stderr)
        return 1

    print(f"      Device      : {device.name}")
    print(f"      CPU         : {device.cpu_name or 'N/A'}")
    print(f"      Peripherals : {len(device.peripherals)}")

    out_root = Path(args.out_dir)

    if args.output in ("header", "both"):
        print(f"[2/3] Generating C header ...")
        path = generate_header(
            device,
            template_dir=args.templates,
            output_dir=out_root / "headers",
        )
        print(f"      Written → {path}")

    if args.output in ("report", "both"):
        print(f"[3/3] Generating Markdown report ...")
        path = generate_report(
            device,
            template_dir=args.templates,
            output_dir=out_root / "reports",
        )
        print(f"      Written → {path}")

    print("\n✅ Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())