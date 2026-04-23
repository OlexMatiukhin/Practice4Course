import base64
import zipfile
import io

with open('archive_data.txt', 'r') as f:
    read_string = f.read()

# 2. Декодируем строку обратно в "сырые" байты архива
raw_bytes = base64.b64decode(read_string)

# 3. Оборачиваем байты в виртуальный файл (ПЕРЕДАЕМ raw_bytes!)
virtual_file = io.BytesIO(raw_bytes)

# 4. Открываем архив из памяти и работаем с ним
with zipfile.ZipFile(virtual_file, 'r') as zip_ref:
    print("Список файлов внутри:", zip_ref.namelist())

    # Распаковываем всё в нужную папку (например, 'extracted_files' рядом со скриптом)
    zip_ref.extractall('extracted_files')
    print("Архив успешно распакован!")