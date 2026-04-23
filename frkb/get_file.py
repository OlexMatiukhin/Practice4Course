import base64

with open('C:\\Users\\sasha\\Desktop\\Practise_4_course\\pythonProject1\multifile-zip-bomb\\bomb.zip', 'rb') as file:
    archive_bytes = file.read()

encoded_string = base64.b64encode(archive_bytes).decode('utf-8')

# Открываем текстовый файл для записи
with open('bytes.txt', 'w') as f:
    f.write(encoded_string)

    import base64

    # ... (ваш код чтения архива) ...
    encoded_string = base64.b64encode(archive_bytes).decode('utf-8')

    # Генерируем валидный Python-код
    with open('my_archive_data.py', 'w') as f:
        f.write(f'ARCHIVE_BYTES = b"{encoded_string}"\n')