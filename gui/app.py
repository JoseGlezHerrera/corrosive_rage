import logging
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
from datetime import datetime
import subprocess
import os
import threading
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

# ttkbootstrap (tema oscuro chulo, opcional)
try:
    from ttkbootstrap import Style as TtkStyle
    TTKBOOTSTRAP_AVAILABLE = True
except Exception:
    TTKBOOTSTRAP_AVAILABLE = False

STRINGS = {
    'window_title': "Corrosive's Rage - OSINT Toolkit",
    'target_label': "Objetivo:",
    'run_button': "¡Investigar!",
    'clear_button': "Limpiar",
    'results_label': "Resultados de la Investigación",
    'status_ready': "Listo para investigar",
    'status_running': "Ejecutando investigación...",
    'status_canceling': "Cancelando...",
    'about_text': "Corrosive's Rage - OSINT Toolkit\nVersión 1.0",
    'error_no_target': "Debes introducir un objetivo.",
    'error_no_module': "Debes seleccionar al menos un módulo.",
    'no_results_folder': "No existe la carpeta 'results'. Ejecuta algo primero.",
    'no_results_files': "No se encontraron archivos de resultados.",
    'pdf_ok': "Informe PDF generado correctamente.",
    'pdf_fail': "No se pudo generar el PDF.",
    'module_translations': {
        'domain_recon': 'Análisis de Dominio',
        'email_recon': 'Análisis de Email',
        'ip_recon': 'Análisis de IP',
        'username_recon': 'Búsqueda de Usuario',
        'breach_recon': 'Búsqueda de Leaks',
        'company_recon': 'Recon. de Empresa',
        'metadata_recon': 'Análisis de Metadatos',
        'dork_recon': 'Búsqueda con Dorks',
        'phone_recon': 'Análisis de Teléfono',
    }
}

ASCII_HEADER = r"""
_________                                  .__           /\         __________                        
\_   ___ \  __________________  ____  _____|__|__  __ ___)/  ______ \______   \_____     ____   ____  
/    \  \/ /  _ \_  __ \_  __ \/  _ \/  ___/  \  \/ // __ \ /  ___/  |       _/\__  \   / ___\_/ __ \ 
\     \___(  <_> )  | \/|  | \(  <_> )___ \|  |\   /\  ___/ \___ \   |    |   \ / __ \_/ /_/  >  ___/ 
 \______  /\____/|__|   |__|   \____/____  >__| \_/  \___  >____  >  |____|_  /(____  /\___  / \___  >
        \/                               \/              \/     \/          \/      \//_____/      \/ 
"""

SPINNER_FRAMES = ["▖", "▘", "▝", "▗"]


class OsintGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(STRINGS["window_title"])
        self.root.geometry("1280x800")
        self.root.minsize(1100, 650)

        self.target_var = tk.StringVar()
        self.status_var = tk.StringVar(value=STRINGS["status_ready"])
        self.spinner_var = tk.StringVar(value="")
        self.current_theme = "dark"
        self.running = False
        self.last_run_files = []  # lista de JSON usados en la última ejecución

        # logging básico
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("CorrosiveGUI")

        # Tema / fuentes
        if TTKBOOTSTRAP_AVAILABLE:
            try:
                self.style = TtkStyle(theme="cyborg")
            except Exception:
                self.style = ttk.Style(self.root)
        else:
            self.style = ttk.Style(self.root)

        self.base_font = font.nametofont("TkDefaultFont").copy()
        self.base_font.configure(size=10)
        self.mono_font = ("Consolas", 10) if sys.platform == "win32" else ("DejaVu Sans Mono", 10)

        # Inicializamos estructuras
        self.module_vars = {}
        self.modules_list = self.scan_modules()

        # Construimos UI
        self.build_menu()
        self.build_layout()
        self.apply_theme("dark")

        # arrancar animación spinner (solo se mueve si self.running == True)
        self.root.after(120, self._spinner_tick)

    # ============================================================
    #   UI BASICA
    # ============================================================

    def build_menu(self):
        menubar = tk.Menu(self.root)

        # Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir carpeta de resultados", command=self.open_results_folder)
        file_menu.add_command(label="Abrir último JSON", command=self.open_last_json_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Tema
        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Modo oscuro", command=lambda: self.apply_theme("dark"))
        theme_menu.add_command(label="Modo claro", command=lambda: self.apply_theme("light"))
        menubar.add_cascade(label="Tema", menu=theme_menu)

        # Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.root.config(menu=menubar)

    def build_layout(self):
        # Layout: columna 0 = dock lateral, columna 1 = contenido
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # ---------- Dock lateral ----------
        dock = ttk.Frame(self.root, padding=4)
        dock.grid(row=0, column=0, sticky="ns")

        ttk.Label(dock, text="Dock", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, pady=(4, 8))

        ttk.Button(dock, text="📁 Resultados", width=18,
                   command=self.open_results_folder).grid(row=1, column=0, pady=2)
        ttk.Button(dock, text="📄 Último JSON", width=18,
                   command=self.open_last_json_file).grid(row=2, column=0, pady=2)
        ttk.Button(dock, text="🧾 Exportar PDF", width=18,
                   command=self.export_pdf_report).grid(row=3, column=0, pady=2)
        ttk.Button(dock, text="⚙ Config (info)", width=18,
                   command=self.show_config_info).grid(row=4, column=0, pady=10)

        # ---------- Contenido principal ----------
        main = ttk.Frame(self.root, padding=6)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        # ASCII header
        ascii_lbl = tk.Label(
            main,
            text=ASCII_HEADER.strip(),
            font=self.mono_font,
            fg="#00FF41",
            bg="#0b0b0b",
            justify="left",
            anchor="w"
        )
        ascii_lbl.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 6))

        # FORM
        form = ttk.Frame(main)
        form.grid(row=1, column=0, sticky="ew", padx=4)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text=STRINGS["target_label"]).grid(row=0, column=0, sticky="w", padx=(0, 4))
        target_entry = ttk.Entry(form, textvariable=self.target_var)
        target_entry.grid(row=0, column=1, sticky="w", padx=(0, 6))
        target_entry.configure(width=50)

        # multi-modulo: checkbuttons
        modules_frame = ttk.Frame(form)
        modules_frame.grid(row=0, column=2, padx=(10, 6))
        ttk.Label(modules_frame, text="Módulos:").grid(row=0, column=0, sticky="w")

        self.module_vars = {}
        row_index = 1
        for mod in self.modules_list:
            alias = STRINGS["module_translations"].get(mod, mod)
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(modules_frame, text=alias, variable=var)
            chk.grid(row=row_index, column=0, sticky="w")
            self.module_vars[mod] = var
            row_index += 1

        # seleccionar todos
        self.select_all_var = tk.BooleanVar(value=False)
        sel_all_chk = ttk.Checkbutton(
            modules_frame,
            text="(Seleccionar todos)",
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        sel_all_chk.grid(row=row_index, column=0, sticky="w", pady=(4, 0))

        # Botones acción
        buttons_frame = ttk.Frame(form)
        buttons_frame.grid(row=0, column=3, padx=(10, 0))

        self.run_button = ttk.Button(buttons_frame, text=STRINGS["run_button"],
                                     command=self.start_investigation, width=14)
        self.run_button.grid(row=0, column=0, pady=2)

        self.clear_button = ttk.Button(buttons_frame, text=STRINGS["clear_button"],
                                       command=self.clear_output, width=14)
        self.clear_button.grid(row=1, column=0, pady=2)

        # Spinner label (ASCII anim) encima de resultados
        self.spinner_label = ttk.Label(main, textvariable=self.spinner_var)
        self.spinner_label.grid(row=2, column=0, sticky="w", padx=4, pady=(4, 0))

        # CONTENEDOR RESULTADOS
        results_container = ttk.Frame(main)
        results_container.grid(row=3, column=0, sticky="nsew", padx=4, pady=(4, 4))
        results_container.columnconfigure(0, weight=1)
        results_container.rowconfigure(1, weight=3)
        results_container.rowconfigure(2, weight=2)

        ttk.Label(results_container, text=STRINGS["results_label"]).grid(row=0, column=0, sticky="w")

        self.output_text = scrolledtext.ScrolledText(results_container, wrap="word", height=18, state="disabled")
        self.output_text.grid(row=1, column=0, sticky="nsew", pady=(2, 4))

        self.results_preview = scrolledtext.ScrolledText(results_container, wrap="word", height=8, state="disabled")
        self.results_preview.grid(row=2, column=0, sticky="nsew")

        # Barra progreso + status
        status_frame = ttk.Frame(main)
        status_frame.grid(row=4, column=0, sticky="ew", padx=4, pady=(2, 0))
        status_frame.columnconfigure(1, weight=1)

        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=250)
        self.progress.grid(row=0, column=0, sticky="w")

        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor="w", relief="sunken")
        status_label.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # root row weights
        main.rowconfigure(3, weight=1)

    # ============================================================
    #   THEMING
    # ============================================================

    def apply_theme(self, theme: str):
        self.current_theme = theme
        if theme == "dark":
            bg_root = "#0b0b0b"
            txt_bg = "#020202"
            txt_fg = "#00FF41"
        else:  # light
            bg_root = "#f0f0f0"
            txt_bg = "#ffffff"
            txt_fg = "#000000"

        self.root.configure(bg=bg_root)
        for widget in [self.output_text, self.results_preview]:
            try:
                widget.configure(bg=txt_bg, fg=txt_fg, insertbackground=txt_fg)
            except Exception:
                pass

    # ============================================================
    #   LOGICA
    # ============================================================

    def scan_modules(self):
        mods_dir = PROJECT_ROOT / "src" / "corrosive_rage" / "modules"
        modules = []
        if mods_dir.exists():
            for py in mods_dir.glob("*.py"):
                if not py.name.startswith("_"):
                    modules.append(py.stem)
        return modules

    def toggle_select_all(self):
        value = self.select_all_var.get()
        for var in self.module_vars.values():
            var.set(value)

    def get_selected_modules(self):
        return [name for name, var in self.module_vars.items() if var.get()]

    # ============================================================

    def start_investigation(self):
        target = self.target_var.get().strip()
        modules = self.get_selected_modules()

        if not target:
            messagebox.showerror("ERROR", STRINGS["error_no_target"])
            return
        if not modules:
            messagebox.showerror("ERROR", STRINGS["error_no_module"])
            return

        self.clear_output()
        self.update_output(f"[*] Iniciando investigación para objetivo: '{target}'\n")
        self.update_output(f"[*] Módulos seleccionados: {', '.join(modules)}\n\n")

        self.run_button.config(state="disabled")
        self.running = True
        self.progress.start(10)
        self.status_var.set(STRINGS["status_running"])
        self.last_run_files = []

        thread = threading.Thread(target=self._run_modules_thread, args=(target, modules), daemon=True)
        thread.start()

    def _run_modules_thread(self, target, modules):
        try:
            for idx, mod in enumerate(modules, start=1):
                self.update_output(f"\n[+] Ejecutando módulo {idx}/{len(modules)}: {mod}\n\n")
                self.run_single_module(target, mod)
        finally:
            self.running = False
            self.progress.stop()
            self.run_button.config(state="normal")
            self.status_var.set(STRINGS["status_ready"])
            self.spinner_var.set("")

    # ============================================================
    #   EJECUCIÓN DE UN MÓDULO + CARGA DE JSON
    # ============================================================

    def run_single_module(self, target, module):
        interpreter = sys.executable or "python"
        base_dir = PROJECT_ROOT
        results_dir = PROJECT_ROOT / "results"
        results_dir.mkdir(exist_ok=True)

        cmd = [interpreter, "-m", "corrosive_rage", "-t", target, "-m", module]

        env = os.environ.copy()
        env["PYTHONPATH"] = str(base_dir / "src")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=base_dir,
                bufsize=1,
                env=env
            )

            for line in iter(process.stdout.readline, ""):
                if not line:
                    break
                self.update_output(line)

            process.stdout.close()
            process.wait()

            # Buscar el JSON más reciente asociado a este target y módulo
            files = list(results_dir.glob("*.json"))
            if not files:
                self.update_output("[i] No hay archivos JSON en 'results'.\n")
                return

            safe_target_variants = {
                target.lower(),
                target.replace(".", "_").lower(),
                self._safe_target(target).lower()
            }
            module_flat = module.replace("_", "").lower()

            matches = []
            for f in files:
                stem_low = f.stem.lower()
                stem_flat = stem_low.replace("_", "").replace("-", "")
                if any(tv in stem_low for tv in safe_target_variants) and module_flat in stem_flat:
                    matches.append(f)

            if matches:
                latest = max(matches, key=lambda f: f.stat().st_mtime)
                self.last_run_files.append(latest)
                try:
                    data = json.loads(latest.read_text(encoding="utf-8"))
                    self.show_json(data)
                    self.update_output(f"[+] Resultado cargado: {latest.name}\n")
                except Exception as e:
                    self.update_output(f"[!] Error leyendo JSON {latest.name}: {e}\n")
            else:
                # No damos el coñazo con mensajes de error: simplemente informativo
                self.update_output("[i] No se encontró un JSON asociado a este módulo (puede haberse guardado con otro nombre).\n")

        except Exception as e:
            self.update_output(f"\n[!] Error ejecutando módulo {module}: {e}\n")

    # ============================================================

    def _safe_target(self, target: str) -> str:
        return "".join(c if c.isalnum() or c == "_" else "_" for c in target.replace(".", "_"))

    # ============================================================

    def update_output(self, text: str):
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")

    def show_json(self, data: dict):
        self.results_preview.config(state="normal")
        self.results_preview.delete("1.0", tk.END)
        self.results_preview.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
        self.results_preview.config(state="disabled")

    def clear_output(self):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")

        self.results_preview.config(state="normal")
        self.results_preview.delete("1.0", tk.END)
        self.results_preview.config(state="disabled")

    # ============================================================
    #   SPINNER ANIM
    # ============================================================

    def _spinner_tick(self, idx=0):
        if self.running:
            frame = SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]
            self.spinner_var.set(f"{frame} {STRINGS['status_running']}")
            self.root.after(120, self._spinner_tick, idx + 1)
        else:
            self.spinner_var.set("")
            self.root.after(200, self._spinner_tick, 0)

    # ============================================================
    #   ACCIONES EXTRA: RESULTADOS / PDF
    # ============================================================

    def open_results_folder(self):
        results_dir = PROJECT_ROOT / "results"
        if not results_dir.exists():
            messagebox.showinfo("Info", STRINGS["no_results_folder"])
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(results_dir)  # type: ignore
            elif sys.platform == "darwin":
                subprocess.Popen(["open", results_dir])
            else:
                subprocess.Popen(["xdg-open", results_dir])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}")

    def open_last_json_file(self):
        results_dir = PROJECT_ROOT / "results"
        if not results_dir.exists():
            messagebox.showinfo("Info", STRINGS["no_results_folder"])
            return

        files = list(results_dir.glob("*.json"))
        if not files:
            messagebox.showinfo("Info", STRINGS["no_results_files"])
            return

        latest = max(files, key=lambda f: f.stat().st_mtime)

        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            self.show_json(data)

            if sys.platform.startswith("win"):
                os.startfile(latest)  # type: ignore
            elif sys.platform == "darwin":
                subprocess.Popen(["open", latest])
            else:
                subprocess.Popen(["xdg-open", latest])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")

    def export_pdf_report(self):
        # Si no hay lista de archivos de esta sesión, intentamos inferirlos de la carpeta results
        if not self.last_run_files:
            results_dir = PROJECT_ROOT / "results"
            if not results_dir.exists():
                messagebox.showinfo(
                    "Info",
                    "No hay carpeta 'results'. Ejecuta algún módulo antes de exportar."
                )
                return

            files = sorted(results_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            if not files:
                messagebox.showinfo(
                    "Info",
                    "No hay archivos JSON en la carpeta 'results'."
                )
                return

            current_target = self.target_var.get().strip()
            if current_target:
                safe_target = self._safe_target(current_target).replace(".", "_").lower()
                filtered = [f for f in files if safe_target in f.stem.lower()]
            else:
                filtered = []

            selected = filtered or files[:5]
            self.last_run_files = selected

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except Exception:
            messagebox.showerror(
                "Error",
                "No se encontró la librería 'reportlab'.\nInstálala con:\n\npip install reportlab"
            )
            return

        reports_dir = PROJECT_ROOT / "reports"
        reports_dir.mkdir(exist_ok=True)

        target = self._safe_target(self.target_var.get().strip() or "target")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = reports_dir / f"corrosive_report_{target}_{timestamp}.pdf"

        try:
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("Corrosive's Rage - Informe OSINT", styles["Title"]))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Objetivo: {self.target_var.get().strip()}", styles["Normal"]))
            story.append(Paragraph(
                f"Fecha: {datetime.now().isoformat(sep=' ', timespec='seconds')}",
                styles["Normal"]
            ))
            story.append(Spacer(1, 18))

            for json_file in self.last_run_files:
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                except Exception as e:
                    story.append(Paragraph(
                        f"Error leyendo {json_file.name}: {e}",
                        styles["Normal"]
                    ))
                    story.append(Spacer(1, 12))
                    continue

                story.append(Paragraph(f"Módulo: {data.get('module', 'N/A')}", styles["Heading2"]))
                story.append(Paragraph(f"Archivo: {json_file.name}", styles["Normal"]))
                story.append(Spacer(1, 6))

                pretty = json.dumps(data, indent=2, ensure_ascii=False)
                for line in pretty.splitlines():
                    story.append(Paragraph(line.replace(" ", "&nbsp;"), styles["Code"]))
                story.append(Spacer(1, 12))

            doc.build(story)

            messagebox.showinfo("OK", f"{STRINGS['pdf_ok']}\n\n{pdf_path}")
            try:
                if sys.platform.startswith("win"):
                    os.startfile(pdf_path)  # type: ignore
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", pdf_path])
                else:
                    subprocess.Popen(["xdg-open", pdf_path])
            except Exception:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"{STRINGS['pdf_fail']}\n\n{e}")

    # ============================================================

    def show_config_info(self):
        config_path = PROJECT_ROOT / "config" / "config.ini"
        msg = f"Archivo de configuración esperado en:\n\n{config_path}\n\n" \
              f"Edita ese fichero para añadir tus claves de API (Shodan, HIBP, etc.)."
        messagebox.showinfo("Config", msg)

    def show_about(self):
        messagebox.showinfo("Acerca de", STRINGS["about_text"])


# ============================================================
#   MAIN
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = OsintGui(root)
    root.mainloop()