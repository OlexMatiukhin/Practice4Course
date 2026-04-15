import zlib
import zipfile
import math
import os
import shutil
import sys
import time
import argparse
import zipfile
import os
from multiprocessing import Pool

def add_file_to_zip(zf, path, include_dir=True):
	"""Add directory to zip file"""
	if os.path.isfile(path):
		zf.write(path, compress_type=zipfile.ZIP_DEFLATED)
	elif os.path.isdir(path):
		for root, dirs, files in os.walk(path):
			arc_root = root
			if not include_dir:
				arc_root = root[len(path):]
				if arc_root.startswith(os.sep):
					arc_root = arc_root[1:]
			for file in files:
				zf.write(os.path.join(root, file), arcname=os.path.join(arc_root, file))


def make_zip_flat(size, out_file, include_dirs, include_files):
    dummy_name_format = 'dummy{}.txt'
    files_nb = max(1, int(size / 100))
    print(files_nb)
    file_size = int(size / files_nb)
    last_file_size = size - (file_size * files_nb)

    if os.path.isfile(out_file):
        os.remove(out_file)

    chunk = b'0' * (1024 * 1024)
    with zipfile.ZipFile(out_file, mode='w', allowZip64=True) as zf:
        for f in include_dirs:
            add_file_to_zip(zf, f, include_dir=False)
        for f in include_files:
            add_file_to_zip(zf, f)
        for i in range(files_nb):
            print(i)
            name = dummy_name_format.format(i)
            with zf.open(name, 'w', force_zip64=True) as entry:
                for _ in range(file_size):
                    entry.write(chunk)

        if last_file_size > 0:
            name = dummy_name_format.format(files_nb)
            with zf.open(name, 'w', force_zip64=True) as entry:
                for _ in range(last_file_size):
                    entry.write(chunk)

    return files_nb * file_size




MAX_PART_SIZE_MB = 1024  # максимум 1 ГБ на один zip-файл


def compress_one_part(args):
    """Сжимает один кусок данных в отдельный zip"""
    part_index, size_mb = args
    chunk = b'0' * (64 * 1024 * 1024)  # 64 MB чанк

    tmp_path = f"tmp_part_{part_index}.bin"
    zip_path = f"part_{part_index}.zip"

    with open(tmp_path, 'wb') as f:
        remaining = size_mb * 1024 * 1024
        while remaining > 0:
            write_size = min(len(chunk), remaining)
            f.write(chunk[:write_size])
            remaining -= write_size

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        zf.write(tmp_path, f"dummy_{part_index}.txt")

    os.remove(tmp_path)
    print(f"  Часть {part_index} готова")
    return zip_path


def make_zip_fast(total_size_mb, out_file, workers=None):
    if workers is None:
        workers = os.cpu_count()

    # Разбиваем total_size_mb на части по MAX_PART_SIZE_MB
    num_parts = (total_size_mb + MAX_PART_SIZE_MB - 1) // MAX_PART_SIZE_MB

    # Размеры всех частей
    parts = []
    remaining = total_size_mb
    for i in range(num_parts):
        part_size = min(MAX_PART_SIZE_MB, remaining)
        parts.append((i, part_size))
        remaining -= part_size

    print(f"Всего частей: {num_parts}, ядер: {workers}")
    print(f"Каждое ядро обработает ~{num_parts // workers} частей")

    # Параллельно сжимаем, пул сам распределяет задачи по ядрам
    with Pool(workers) as pool:
        part_zips = pool.map(compress_one_part, parts)

    # Объединяем все zip-части в один финальный архив
    print("Объединяем части...")
    with zipfile.ZipFile(out_file, 'w', allowZip64=True) as out_zf:
        for part_zip in part_zips:
            with zipfile.ZipFile(part_zip, 'r') as part_zf:
                for name in part_zf.namelist():
                    # Читаем уже сжатые данные напрямую, без повторного сжатия
                    zinfo = part_zf.getinfo(name)
                    with part_zf.open(zinfo) as src:
                        out_zf.writestr(zinfo, src.read())
            os.remove(part_zip)
            print(f"  Добавлен {part_zip}")

    print("Готово!")








def help_epilog():
	return """mode of compression options:
  flat - flat zip file with contents
  nested - nested zip file, zip of zips of zips ... (much smaller) """


def check_size(value):
	ivalue = int(value)
	if ivalue < 100:
		raise argparse.ArgumentTypeError("%s is an invalid value (< 100)." % value)
	return ivalue




if __name__ == '__main__':

    #args = parser()

    out_zip_file = "result.zip"

    #include_dirs = [d.strip() for d in args.dirs.strip().split(',') if d != '']
    #include_files = [d.strip() for d in args.files.strip().split(',') if d != '']
    size = 30000

    start_time = time.time()
    mode ="flat"

    if mode == 'flat':
        #actual_size = make_zip_flat(size, out_zip_file, include_dirs=[], include_files=[])
        make_zip_fast(total_size_mb=1_145_728, out_file="result.zip", workers=os.cpu_count())
    #else:
        #actual_size = make_zip_nested(size, out_zip_file, include_dirs=[],  include_files=[])
    end_time = time.time()
    print('Compressed File Size: %.2f KB'%(os.stat(out_zip_file).st_size/1024.0))
    #print('Size After Decompression: %d MB'%actual_size)
    print('Generation Time: %.2fs'%(end_time - start_time))
