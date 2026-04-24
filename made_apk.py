import re
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def slugify_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9_]', '', name)
    if not name:
        raise ValueError("Ім'я пакета порожнє. Використай латиницю, цифри або _.")
    return name


def run_command(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, **kwargs)
    except FileNotFoundError:
        raise EnvironmentError(f"Команда '{cmd[0]}' не знайдена.")


def check_requirements():
    # ── briefcase ──
    result = run_command(
        [sys.executable, "-m", "briefcase", "--version"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Встановлюю briefcase...")
        run_command([sys.executable, "-m", "pip", "install", "briefcase"])
        print("✓ briefcase встановлено")
    else:
        print(f"✓ briefcase: {result.stdout.strip()}")

    # ── Java ──
    try:
        java = run_command(["java", "-version"], capture_output=True, text=True)
        if java.returncode != 0:
            raise EnvironmentError("Java повернула помилку під час перевірки версії.")
        version_line = (java.stderr or java.stdout).splitlines()[0] if (java.stderr or java.stdout) else "?"
        print(f"✓ Java: {version_line}")
    except EnvironmentError:
        raise EnvironmentError(
            "\n✗ Java JDK не знайдена!\n"
            "1. Завантаж JDK 17: https://adoptium.net/\n"
            "2. Встанови з галочкою 'Add to PATH'\n"
            "3. Перезапусти PyCharm/термінал"
        )


def write_app_module(app_dir: Path, module_name: str):
    """Генерує мінімальний toga-застосунок."""
    src_dir = app_dir / "src" / module_name
    src_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py — точка входу для briefcase
    (src_dir / "__init__.py").write_text(
        f'from {module_name}.app import main\n',
        encoding="utf-8"
    )
    # app.py — toga UI
    (src_dir / "app.py").write_text(
        'import toga\n'
        'from toga.style import Pack\n'
        'from toga.style.pack import COLUMN\n'
        'from . import tolk1\n'  
        '\n'
        'def build(app):\n'
        '    main_box = toga.Box(style=Pack(direction=COLUMN, padding=20))\n'
        '\n'
        '    tolk1.main()  # запускаємо твій скрипт\n'
        '\n'
        '    return main_box\n'
        '\n'
        'def main():\n'
        '    return toga.App(\n'
        '        "Мій застосунок",\n'
        '        "org.example.app",\n'
        '        startup=build\n'
        '    )\n',
        encoding="utf-8"
    )

def write_pyproject_toml(app_dir: Path, title: str, package_name: str,
                          package_domain: str, icon_png: str):
    icon_path = str(Path(icon_png).with_suffix("")).replace("\\", "/")

    toml = f"""[tool.briefcase]
project_name = "{title}"
bundle = "{package_domain}"
version = "1.0.0"
url = "https://example.com"
license.text = "MIT"
author = "Author"
author_email = "author@example.com"

[tool.briefcase.app.{package_name}]
formal_name = "{title}"
description = "{title} Android App"
icon = "{icon_path}"
sources = [
    "src/{package_name}",
]
requires = [
    "toga",
]

[tool.briefcase.app.{package_name}.android]
requires = []
build_gradle_dependencies = [
    "androidx.appcompat:appcompat:1.0.2",
    "androidx.constraintlayout:constraintlayout:1.1.3",
    "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
]
"""
    (app_dir / "pyproject.toml").write_text(toml, encoding="utf-8")


def prepare_project(icon_src: Path, build_name: str, script: Path) -> Path:

    file_name = script.name
    if not Path(script).exists():
        raise FileNotFoundError(f"Скрипт '{script}' не знайдено.")
    if not icon_src.exists():
        raise FileNotFoundError(f"Іконка '{icon_src}' не знайдена.")

    app_dir = Path("android_app")
    app_dir.mkdir(exist_ok=True)

    package_name = slugify_name(build_name)

    # Копіюємо скрипт у src/package_name/
    src_pkg_dir = app_dir / "src" / package_name
    src_pkg_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script, src_pkg_dir / file_name)

    # Копіюємо іконку
    icon_dst_dir = app_dir / "icons"
    icon_dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(icon_src, icon_dst_dir / icon_src.name)

    write_app_module(app_dir, package_name)
    write_pyproject_toml(
        app_dir=app_dir,
        title=build_name,
        package_name=package_name,
        package_domain="org.example",
        icon_png=str(icon_src),
    )

    print(f"✓ Проєкт підготовлено: {app_dir.resolve()}")
    return app_dir


def run_briefcase_step(step: str, app_dir: Path):
    print(f"\n{'='*55}")
    print(f"  briefcase {step} android")
    print(f"{'='*55}\n")
    result = run_command(
        [sys.executable, "-m", "briefcase", step, "android", "-v"],
        cwd=app_dir
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"\n✗ briefcase {step} завершився з помилкою (код: {result.returncode})\n"
            f"Подивись на логи ВИЩЕ — там є реальна причина.\n"
            f"Найчастіші причини:\n"
            f"  • Java не встановлена або стара (потрібна 17+)\n"
            f"  • Немає місця на диску (потрібно ~5 ГБ)\n"
            f"  • Антивірус блокує завантаження Android SDK\n"
            f"  • Проблеми з інтернетом при завантаженні SDK"
        )


def build_apk(app_dir: Path):
    app_dir = Path(app_dir).resolve()
    run_briefcase_step("create", app_dir)
    run_briefcase_step("build", app_dir)
    apk_files = list((app_dir / "build").rglob("*.apk"))
    build_dir = app_dir / "build"
    if apk_files:
        print("\n✓ Збірка APK успішна!")
        for apk in apk_files:
            dist_dir = Path("dist")
            dist_dir.mkdir(exist_ok=True)
            shutil.move(apk, dist_dir/apk.name)
            shutil.rmtree("android_app")
            print(f"dist/{apk.name}")
    else:
        print(f"\n APK не знайдено у {build_dir}")
        shutil.rmtree("android_app")



if __name__ == "__main__":
    check_requirements()

    name = input("Введіть ім'я файлу: ")
    if (len(name) == 0):
        raise ValueError("Ім'я")
    decision = input("Використовувати вбудовану іконку? у/n: ").strip().lower()
    if (decision == "y"):
        doc_type = input("Введіть тип іконки (pdf/word): ").strip().lower()
        icon_map = {
            "pdf": BASE_DIR / "icons" / "pdf.png",
            "word": BASE_DIR / "icons" / "word.png",
        }
        if doc_type not in icon_map:
            raise ValueError("Потрібно ввести pdf/word")
        icon_src = Path(icon_map[doc_type])
    elif decision == "n":
        icon_src = Path(input("Введіть шлях до вашої іконки (наприклад, C:/my_icons/custom.ico): ").strip())
    else:
        raise ValueError("Потрібно ввести 'y' або 'n'")
        
    script_path = BASE_DIR / "frkb" / "tolk2.py"
    app_dir = prepare_project(icon_src, name, script=script_path)
    build_apk(app_dir)
