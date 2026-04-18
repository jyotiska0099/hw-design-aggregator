# src/parser.py
from __future__ import annotations
from pathlib import Path
from typing import Optional
from lxml import etree
from src.models import Device, Peripheral, Register, BitField


def _text(el: etree._Element, tag: str) -> Optional[str]:
    """Safely extract text from a child element."""
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else None


def _int(el: etree._Element, tag: str) -> Optional[int]:
    """Extract an integer (handles hex like 0x40013800 and decimal)."""
    val = _text(el, tag)
    if val is None:
        return None
    val = val.strip().lower().replace(" ", "")
    try:
        return int(val, 0)   # int(x, 0) auto-detects 0x hex / decimal
    except ValueError:
        return None


def _parse_fields(register_el: etree._Element) -> list[BitField]:
    fields = []
    fields_el = register_el.find("fields")
    if fields_el is None:
        return fields

    for f in fields_el.findall("field"):
        name = _text(f, "name") or "UNKNOWN"
        bit_offset = _int(f, "bitOffset")
        bit_width  = _int(f, "bitWidth")

        # Some SVDs use <bitRange>[7:4]</bitRange> instead
        if bit_offset is None or bit_width is None:
            bit_range = _text(f, "bitRange")
            if bit_range:
                high, low = bit_range.strip("[]").split(":")
                bit_offset = int(low)
                bit_width  = int(high) - int(low) + 1

        if bit_offset is None or bit_width is None:
            continue   # skip malformed fields

        # Optional enumerated values
        enum_values: dict[str, int] = {}
        enum_el = f.find("enumeratedValues")
        if enum_el is not None:
            for ev in enum_el.findall("enumeratedValue"):
                ev_name = _text(ev, "name")
                ev_val  = _int(ev, "value")
                if ev_name and ev_val is not None:
                    enum_values[ev_name] = ev_val

        fields.append(BitField(
            name        = name,
            description = _text(f, "description"),
            bit_offset  = bit_offset,
            bit_width   = bit_width,
            access      = _text(f, "access"),
            enum_values = enum_values,
        ))

    return fields


def _parse_registers(peripheral_el: etree._Element) -> list[Register]:
    registers = []
    registers_el = peripheral_el.find("registers")
    if registers_el is None:
        return registers

    for r in registers_el.findall("register"):
        name = _text(r, "name") or "UNKNOWN"
        address_offset = _int(r, "addressOffset")
        if address_offset is None:
            continue

        registers.append(Register(
            name           = name,
            description    = _text(r, "description"),
            address_offset = address_offset,
            size           = _int(r, "size") or 32,
            access         = _text(r, "access"),
            reset_value    = _int(r, "resetValue"),
            fields         = _parse_fields(r),
        ))

    return registers


def _parse_peripherals(device_el: etree._Element) -> list[Peripheral]:
    peripherals = []
    peripherals_el = device_el.find("peripherals")
    if peripherals_el is None:
        return peripherals

    # First pass: build a map of name → element for derivedFrom resolution
    peripheral_map: dict[str, etree._Element] = {}
    for p in peripherals_el.findall("peripheral"):
        pname = _text(p, "name") or ""
        peripheral_map[pname] = p

    for p in peripherals_el.findall("peripheral"):
        name = _text(p, "name") or "UNKNOWN"
        base_address = _int(p, "baseAddress")
        if base_address is None:
            continue

        # Handle derivedFrom — inherit registers from a base peripheral
        derived_from = p.get("derivedFrom")
        if derived_from and derived_from in peripheral_map:
            source_el = peripheral_map[derived_from]
            registers = _parse_registers(source_el)
        else:
            registers = _parse_registers(p)

        peripherals.append(Peripheral(
            name         = name,
            description  = _text(p, "description"),
            base_address = base_address,
            group_name   = _text(p, "groupName"),
            registers    = registers,
        ))

    return peripherals


def parse_svd(path: str | Path) -> Device:
    """Parse an SVD file and return a fully populated Device model."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SVD file not found: {path}")

    tree = etree.parse(str(path))
    device_el = tree.getroot()

    return Device(
        name               = _text(device_el, "name") or path.stem,
        version            = _text(device_el, "version"),
        description        = _text(device_el, "description"),
        cpu_name           = _text(device_el.find("cpu"), "name") if device_el.find("cpu") is not None else None,
        address_unit_bits  = _int(device_el, "addressUnitBits") or 8,
        width              = _int(device_el, "width") or 32,
        peripherals        = _parse_peripherals(device_el),
    )