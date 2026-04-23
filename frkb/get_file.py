import base64

with open('C:\\Users\\sasha\\Desktop\\Practise_4_course\\pythonProject1\\fff.zip', 'rb') as file:
    archive_bytes = file.read()

encoded_string = base64.b64encode(archive_bytes).decode('utf-8')


with open('my_archive_data.py', 'w') as f:
    f.write(f'ARCHIVE_BYTES = b"{encoded_string}"\n')