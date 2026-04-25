"""
Скрипт для збирання main.py у EXE за допомогою PyInstaller.
"""

import subprocess
import sys
from pathlib import Path
def main():
    # Встановлюємо PyInstaller, якщо ще не встановлений
    print("📦 Перевіряю / встановлюю PyInstaller...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller"],
        check=True,
    )

    # Команда збірки
    # Примітка: з frkb включаємо лише потрібні .py файли,
    # щоб уникнути проблем з великими файлами (1.3 ГБ) і пробілами в іменах.
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "ProjectUtilities",
        # Hidden imports для модулів, що імпортуються динамічно
        "--hidden-import", "winreg",
        "--hidden-import", "multiprocessing",
        "--hidden-import", "isal",
        "--hidden-import", "isal.isal_zlib",
        # Скрипти-утиліти
        "--add-data", "made_apk.py;.",
        "--add-data", "made_exe.py;.",
        # Іконки
        "--add-data", "icons;icons",
        # frkb — тільки потрібні скрипти
        "--add-data", "frkb/tolk.py;frkb",
        "--add-data", "frkb/tolk2.py;frkb",
        "--add-data", "frkb/tolk3.py;frkb",
        "--add-data", "frkb/get_file.py;frkb",
        # Інші утиліти
        "--add-data", "multifile-zip-bomb/zip_bomb_multipe.py;multifile-zip-bomb",
        "--add-data", "multifile-zip-bomb/Readme.md;multifile-zip-bomb",
        "--add-binary", "multifile-zip-bomb/backward.pyd;multifile-zip-bomb",
        "--add-data", "one_file_inside_zip_bomb;one_file_inside_zip_bomb",
        "--add-data", "png_bomb;png_bomb",
        "main.py",
    ]

    print("🔨 Запускаю збірку...")
    print(" ".join(cmd))
    
    BASE_DIR = Path(__file__).resolve().parent
    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        print("\n✅ Збірка успішна!")
        print("   EXE файл: dist/ProjectUtilities.exe")
    else:
        print(f"\n❌ Помилка збірки (код {result.returncode})")
if __name__ == "__main__":
    main()
