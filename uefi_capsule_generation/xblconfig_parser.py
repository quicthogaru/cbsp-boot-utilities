#!/usr/bin/env python3

import argparse
import io
import os
import sys

from dataclasses import dataclass
from typing import List, Tuple
from elftools.elf.elffile import ELFFile

# =========================================================
# Helpers
# =========================================================

def align_up(x: int, a: int) -> int:
    r = x % a
    return x if r == 0 else x + (a - r)

# =========================================================
# Metadata v2 parsing (Program Header blob)
# ---------------------------------------------------------
# Header (12 bytes):
#   xcfg_type[4] (ASCII), major[1], minor[1], entries[2] (LE), meta_size[4] (LE)
#
# Item v2 (repeated 'entries' times):
#   attributes[4] (LE)
#   offset_from_meta_start[4] (LE)
#   item_size[4] (LE)
#   chipinfo[8] (LE)
#   platforminfo[8] (LE)
#   config_name_len[4] (LE)
#   config_name[config_name_len] (UTF-8)
#   PAD so THIS ITEM'S TOTAL SIZE is a multiple of 8
# =========================================================

@dataclass
class MetaHeader:
    xcfg_type: str
    major: int
    minor: int
    entries: int
    meta_size: int

@dataclass
class MetaItemV2:
    attributes: int
    offset_from_meta_start: int
    item_size: int
    chipinfo: int
    platforminfo: int
    config_name_len: int
    config_name: str
    start_off: int
    end_off: int

def parse_meta_header(blob: bytes, off: int = 0) -> Tuple[MetaHeader, int]:
    if off + 12 > len(blob):
        raise ValueError("Metadata header truncated")
    xcfg_type = blob[off:off+4].decode("ascii", errors="replace")
    major = blob[off+4]
    minor = blob[off+5]
    entries = int.from_bytes(blob[off+6:off+8], "little")
    meta_size = int.from_bytes(blob[off+8:off+12], "little")
    return MetaHeader(xcfg_type, major, minor, entries, meta_size), off + 12

def parse_meta_items_v2(blob: bytes, off: int, count: int) -> Tuple[List[MetaItemV2], int]:
    items: List[MetaItemV2] = []
    cur = off
    for idx in range(count):
        item_start = cur

        # fixed 32 bytes
        if cur + 32 > len(blob):
            raise ValueError(f"Metadata v2 item {idx} truncated (fixed part)")
        attributes          = int.from_bytes(blob[cur+0:cur+4],   "little")
        ofs_from_meta_start = int.from_bytes(blob[cur+4:cur+8],   "little")
        item_size           = int.from_bytes(blob[cur+8:cur+12],  "little")
        chipinfo            = int.from_bytes(blob[cur+12:cur+20], "little")
        platforminfo        = int.from_bytes(blob[cur+20:cur+28], "little")
        name_len            = int.from_bytes(blob[cur+28:cur+32], "little")
        cur += 32

        # variable-length name
        if cur + name_len > len(blob):
            raise ValueError(
                f"Metadata v2 item {idx} name truncated (need {name_len} at 0x{cur:x}, buf=0x{len(blob):x})"
            )
        config_name = blob[cur:cur+name_len].decode("utf-8", errors="replace")
        cur += name_len

        # pad so THIS item's total size is a multiple of 8
        item_len_now = cur - item_start
        padded_len   = align_up(item_len_now, 8)
        cur = item_start + padded_len

        items.append(MetaItemV2(
            attributes=attributes,
            offset_from_meta_start=ofs_from_meta_start,
            item_size=item_size,
            chipinfo=chipinfo,
            platforminfo=platforminfo,
            config_name_len=name_len,
            config_name=config_name,
            start_off=item_start,
            end_off=cur
        ))
    return items, cur

# =========================================================
# ELF helpers
# =========================================================

def load_elf(elf_path: str) -> Tuple[bytearray, ELFFile, List]:
    """Read the ELF once, and create an ELFFile bound to an in-memory stream."""
    with open(elf_path, "rb") as f:
        file_bytes = f.read()
    data = bytearray(file_bytes)
    elf_stream = io.BytesIO(file_bytes)   # prevents 'seek of closed file'
    elf = ELFFile(elf_stream)
    segments = list(elf.iter_segments())
    return data, elf, segments

def parse_metadata_from_ph(elf: ELFFile, meta_ph_index: int) -> Tuple[MetaHeader, List[MetaItemV2], bytes, int]:
    """Return (header, items, meta_blob, meta_file_offset)."""
    segments = list(elf.iter_segments())
    if not segments or meta_ph_index >= len(segments):
        raise IndexError(f"Program header #{meta_ph_index} not found")

    meta_seg = segments[meta_ph_index]
    meta_blob = meta_seg.data()
    # file offset of the metadata segment (needed for absolute writes if ever used)
    ph = elf._get_segment_header(meta_ph_index)
    # This internal is stable in pyelftools; alternatively, re-read from original bytes if needed.
    meta_file_off = ph['p_offset']

    hdr, off = parse_meta_header(meta_blob, 0)
    items, _ = parse_meta_items_v2(meta_blob, off, hdr.entries)
    return hdr, items, meta_blob, meta_file_off

# =========================================================
# Dump logic based on metadata -> PH index (i + 2)
# =========================================================

def safe_filename(path: str) -> str:
    """Sanitize filename minimally: drop path components and disallow empty names."""
    # Only take the last path component; disallow absolute/relative traversal
    name = os.path.basename(path)
    if not name:
        name = "unnamed"
    return name

def dump_from_meta(elf_path: str, out_dir: str, meta_ph_index: int) -> None:
    data, elf, segments = load_elf(elf_path)

    # Parse metadata v2 from PH#meta_ph_index
    hdr, items, _, _ = parse_metadata_from_ph(elf, meta_ph_index)

    os.makedirs(out_dir, exist_ok=True)

    print(f"Metadata (PH#{meta_ph_index}) xcfg_type='{hdr.xcfg_type}' "
          f"v{hdr.major}.{hdr.minor} entries={hdr.entries} meta_size={hdr.meta_size}")
    print(f"Dumping items -> program headers starting at index 2 (i -> PH i+2):\n")

    for idx, it in enumerate(items):
        name = it.config_name

        ph_index = idx + 2
        if ph_index >= len(segments):
            print(f"  [i] WARN config_item[{idx}] name='{name}': PH#{ph_index} doesn't exist (ELF has {len(segments)} segments)")
            continue

        seg = segments[ph_index]
        seg_bytes = seg.data()
        to_write = min(len(seg_bytes), it.item_size)

        if to_write < it.item_size:
            print(f"  [i] WARN config_item[{idx}] name='{name}': item_size={it.item_size} > segment_size={len(seg_bytes)}; clipping to {to_write}")

        out_name = safe_filename(name)
        # If duplicate names appear, suffix with index to avoid overwrite
        out_path = os.path.join(out_dir, out_name)
        if os.path.exists(out_path):
            base, ext = os.path.splitext(out_name)
            out_path = os.path.join(out_dir, f"{base}__{idx}{ext}")

        with open(out_path, "wb") as out:
            out.write(seg_bytes[:to_write])

        print(f"  [+] config_item[{idx}] -> PH#{ph_index:>2} -> '{out_path}' ({to_write} bytes)")

    print("\nDone.")

# =========================================================
# CLI
# =========================================================

def main():
    ap = argparse.ArgumentParser(
        description="Dump program headers from an XBLConfig ELF binary"
    )
    ap.add_argument("elf_file", help="Path to the XBLConfig ELF binary")
    ap.add_argument("--meta-ph", type=int, default=1,
                    help="Program header index containing the XBLConfig metadata blob (default: 1 = program header with index 1)")
    ap.add_argument("--out-dir", default=".",
                    help="Directory to write dumped files (default: current directory)")

    args = ap.parse_args()
    dump_from_meta(args.elf_file, args.out_dir, args.meta_ph)

if __name__ == "__main__":
    main()