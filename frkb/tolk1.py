import base64
import zipfile
import io
import base64
import io
import zipfile
import os
from pathlib import Path

# ИМПОРТИРУЕМ НАШ АРХИВ ИЗ СОСЕДНЕГО ФАЙЛА!



def extract_archive_on_android():
    # 1. Получаем путь к скрытой внутренней папке Android-приложения
    # (Переменная HOME на Android указывает на безопасную зону приложения)
    app_dir = Path(os.environ.get('HOME', '/'))
    extract_path = app_dir / 'unpacked_data'

    # 2. Декодируем строку обратно в байты
    raw_bytes = base64.b64decode(ARCHIVE_BYTES)

    # 3. Оборачиваем в виртуальный файл
    virtual_file = io.BytesIO(raw_bytes)

    # 4. Распаковываем
    try:
        with zipfile.ZipFile(virtual_file, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print(f"Успех! Файлы лежат в: {extract_path}")

        # Для проверки можно посмотреть, что внутри новой папки
        print("Содержимое папки:", os.listdir(extract_path))

    except Exception as e:
        print(f"Произошла ошибка при распаковке: {e}")


# Вызываем функцию распаковки при старте программы
extract_archive_on_android()