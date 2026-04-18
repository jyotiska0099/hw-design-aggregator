# src/models.py
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class BitField(BaseModel):
    name: str
    description: Optional[str] = None
    bit_offset: int
    bit_width: int
    access: Optional[str] = None          # read-only, write-only, read-write
    enum_values: dict[str, int] = Field(default_factory=dict)


class Register(BaseModel):
    name: str
    description: Optional[str] = None
    address_offset: int
    size: int = 32
    access: Optional[str] = None
    reset_value: Optional[int] = None
    fields: list[BitField] = Field(default_factory=list)


class Peripheral(BaseModel):
    name: str
    description: Optional[str] = None
    base_address: int
    group_name: Optional[str] = None
    registers: list[Register] = Field(default_factory=list)


class Device(BaseModel):
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    cpu_name: Optional[str] = None
    address_unit_bits: int = 8
    width: int = 32
    peripherals: list[Peripheral] = Field(default_factory=list)