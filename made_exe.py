import shutil
import subprocess
import sys
import os
from pathlib import Path


def build_exe(script_path, build_name=None, one_file=True, no_console=True, icon=None):
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                   check=True)

    cmd = [sys.executable, "-m", "PyInstaller"]

    if one_file:
        cmd.append("--onefile")
    if no_console:
        cmd.append("--noconsole")
    if build_name:
        cmd += ["--name", build_name]
    if icon:
        cmd += ["--icon", icon]

    cmd.append(script_path)

    result = subprocess.run(cmd, check=True)

    if result.returncode == 0:
        print("Збірка успішна!")
        print(f"Файл знаходиться в: dist/{build_name}.exe")
    else:
        print("Помилки збірки")

name = input("Введіть ім'я файлу: ")
if(len(name) ==0):
    raise ValueError("Ім'я")
decision = input("Використовувати вбудовану іконку? у/n: ").strip().lower()
if (decision == "y"):
    doc_type = input("Введіть тип іконки (pdf/word): ").strip().lower()
    icon_map = {
        "pdf": "icons/pdf.ico",
        "word": "icons/word.ico",
    }
    if doc_type not in icon_map:
        raise ValueError("Потрібно ввести pdf/word")
    icon_src = Path(icon_map[doc_type])
elif decision == "n":
    icon_src = input("Введіть шлях до вашої іконки (наприклад, C:/my_icons/custom.ico): ").strip()
else:
    raise ValueError("Потрібно ввести 'y' або 'n'")

# Використання:
build_exe(
    script_path="frkb/tolk.py",
    build_name=name,
    one_file=True,
    no_console=True,
    icon=icon_src
)

dir_name = "build"

if os.path.exists(dir_name):
    try:
        shutil.rmtree(dir_name)
        print(f"Дерикторія '{dir_name}' та всі її складові успішно видалено.")
    except Exception as e:
        print(f"Помилка при видаленні: {e}")
else:
    print(f"Директорія '{dir_name}' не існує.")




current_dir = Path('.')

spec_files = current_dir.glob('*.spec')

deleted_count = 0

for file_path in spec_files:
    # Перевіряємо, що це дійсно файл, а не папка з таким ім'ям
    if file_path.is_file():
        try:
            file_path.unlink()  # Видаляємо файл
            print(f"Видалено: {file_path.name}")
            deleted_count += 1
        except PermissionError:
            print(f"Немає прав доступу для видалення: {file_path.name}")
        except Exception as e:
            print(f"Помилка при видаленні {file_path.name}: {e}")
if deleted_count == 0:
    print("Файли .spec у поточній директорії не знайдено.")
else:
    print(f"Готово! Всього видалено файлів: {deleted_count}")


