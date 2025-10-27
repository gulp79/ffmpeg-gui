# --- https://g.co/gemini/share/74574d999710 ---

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import ctypes
import subprocess
import threading
import os
import sys
import shutil
import shlex
import re
from pathlib import Path

from tkinterdnd2 import DND_FILES, TkinterDnD

# -----------------------------------------------------------------------------
# PALETTE COLORI STILE MODERNO
# -----------------------------------------------------------------------------
COLOR_PALETTE = {
    "app_bg": "#212121",
    "frame_bg": "#2B2B2B",
    "textbox_bg": "#1b1b1b",
    "accent_green": "#6BFF00",
    "accent_green_hover": "#A8E618",
    "secondary_button": "#555555",
    "secondary_button_hover": "#666666",
    "stop_button": "#880000",
    "stop_button_hover": "#D32F2F",
    "text": "#ffffff",
    "text_dark": "#000000"
}

# -----------------------------------------------------------------------------
# CLASSE PRINCIPALE - AppFrame
# -----------------------------------------------------------------------------

class AppWindow(ctk.CTkToplevel):
    def __init__(self, master, initial_files=None):
        super().__init__(master)
        # Non abbiamo più bisogno di fg_color qui, Toplevel ha già il suo sfondo
        # self.master non è più necessario, perché Toplevel gestisce il suo "master"
        
        # --- IMPOSTAZIONI FINESTRA (spostate qui) ---
        self.title("FFmpeg GUI")
        self.geometry("900x900")
        
        # Configura il layout della griglia direttamente sulla finestra
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.ffmpeg_process = None
        self.is_running = False
        
        # NOTA: Tutti i widget che prima venivano aggiunti a 'self' (che era un Frame)
        # ora verranno aggiunti a 'self' (che è una Toplevel window), quindi il resto 
        # del codice __init__ rimane quasi identico.
        # Esempio: input_frame = ctk.CTkFrame(self, ...) rimane uguale.
        self.ffmpeg_process = None
        self.is_running = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # --- Frame Input File ---
        input_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"])
        input_frame.grid(row=0, column=0, padx=20, pady=(20,10), sticky="nsew")
        input_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(input_frame, text="File da Processare:", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, columnspan=2, padx=10, pady=(5,0), sticky="w")
        self.file_list_box = ctk.CTkTextbox(input_frame, height=150, font=("Segoe UI", 13), fg_color=COLOR_PALETTE["textbox_bg"], text_color=COLOR_PALETTE["text"], border_width=0)
        self.file_list_box.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.file_list_box.drop_target_register(DND_FILES)
        self.file_list_box.dnd_bind('<<Drop>>', self.handle_drop)
        
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        button_frame.grid_columnconfigure((0,1), weight=1)
        
        self.browse_button = ctk.CTkButton(button_frame, text="Aggiungi File", command=self.browse_files, fg_color=COLOR_PALETTE["accent_green"], hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.browse_button.grid(row=0, column=0, padx=(0,5), sticky="ew")
        self.clear_button = ctk.CTkButton(button_frame, text="Pulisci Lista", command=self.clear_file_list, fg_color=COLOR_PALETTE["secondary_button"], hover_color=COLOR_PALETTE["secondary_button_hover"])
        self.clear_button.grid(row=0, column=1, padx=(5,0), sticky="ew")
        
        # --- Frame Opzioni ---
        self.options_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"])
        self.options_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.options_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        ctk.CTkLabel(self.options_frame, text="Codec:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.codec_var = ctk.StringVar(value="AV1")
        self.codec_menu = ctk.CTkOptionMenu(self.options_frame, values=["AV1", "H265", "H264", "Crea proxy"], variable=self.codec_var, command=self.update_ui_for_codec, fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.codec_menu.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.options_frame, text="Preset:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        self.preset_var = ctk.StringVar(value="p5")
        self.preset_menu = ctk.CTkOptionMenu(self.options_frame, values=["p1", "p2", "p3", "p4", "p5", "p6", "p7"], variable=self.preset_var, command=lambda _: self.update_command_preview(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.preset_menu.grid(row=1, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.options_frame, text="CQ (Qualità): 0-Auto, 1-maxQ, 51-minQ", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=2, padx=20, pady=10, sticky="ew")
        self.cq_slider = ctk.CTkSlider(self.options_frame, from_=0, to=51, number_of_steps=52, command=self.update_cq_label, button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], progress_color=COLOR_PALETTE["accent_green"])
        self.cq_slider.set(0)
        self.cq_slider.grid(row=1, column=2, padx=20, pady=5, sticky="ew")
        self.cq_label = ctk.CTkLabel(self.options_frame, text="0", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_PALETTE["accent_green"])
        self.cq_label.grid(row=1, column=3, padx=10, pady=5)
        
        # --- Frame Scaling ---
        self.scaling_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"])
        self.scaling_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.scaling_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.scaling_frame, text="Scaling Output:", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.scale_var = ctk.StringVar(value="Nessuno")        
        self.scale_menu = ctk.CTkOptionMenu(self.scaling_frame, values=["Nessuno", "4k", "2k", "1080p", "720p", "576p", "480p"], variable=self.scale_var, command=lambda _: self.update_command_preview(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.scale_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # --- Frame Anteprima Comando ---
        preview_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"])
        preview_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        preview_header_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
        preview_header_frame.pack(fill="x", padx=10, pady=(5,0))
        ctk.CTkLabel(preview_header_frame, text="Anteprima/Modifica Comando:", font=ctk.CTkFont(weight="bold"), text_color=COLOR_PALETTE["text"]).pack(side="left")
        self.manual_edit_switch = ctk.CTkSwitch(preview_header_frame, text="Modifica Manuale", command=self.toggle_manual_edit_mode, progress_color=COLOR_PALETTE["accent_green"])
        self.manual_edit_switch.pack(side="right")
        self.command_preview = ctk.CTkTextbox(preview_frame, height=100, wrap="none", font=("Courier New", 11), state="disabled", fg_color=COLOR_PALETTE["textbox_bg"], text_color=COLOR_PALETTE["text"], border_width=0)
        self.command_preview.pack(fill="x", expand=True, padx=10, pady=5)
        
        # --- Frame Console di Output con Header e Controlli ---
        console_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"])
        console_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)
        
        console_header = ctk.CTkFrame(console_frame, fg_color="transparent")
        console_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(5,0))
        console_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(console_header, text="Console Output:", font=ctk.CTkFont(weight="bold"), text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, sticky="w")
        
        console_controls = ctk.CTkFrame(console_header, fg_color="transparent")
        console_controls.grid(row=0, column=1, sticky="e")
        
        ctk.CTkLabel(console_controls, text="A capo:", text_color=COLOR_PALETTE["text"]).pack(side="left", padx=(0,5))
        self.wrap_switch = ctk.CTkSwitch(console_controls, text="", width=40, command=self.toggle_wrap, progress_color=COLOR_PALETTE["accent_green"])
        self.wrap_switch.pack(side="left", padx=5)
        
        self.clear_console_button = ctk.CTkButton(console_controls, text="Pulisci", width=80, command=self.clear_console, fg_color=COLOR_PALETTE["secondary_button"], hover_color=COLOR_PALETTE["secondary_button_hover"])
        self.clear_console_button.pack(side="left", padx=5)
        
        self.output_console = ctk.CTkTextbox(console_frame, state="disabled", font=("Courier New", 10), wrap="none", fg_color=COLOR_PALETTE["textbox_bg"], text_color=COLOR_PALETTE["text"], border_width=0)
        self.output_console.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5,10))
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.start_button = ctk.CTkButton(action_frame, text="Avvia Compressione", command=self.start_compression, fg_color=COLOR_PALETTE["accent_green"], hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"], font=ctk.CTkFont(weight="bold"))
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew", ipady=5)
        self.stop_button = ctk.CTkButton(action_frame, text="Ferma Compressione", command=self.stop_compression, fg_color=COLOR_PALETTE["stop_button"], hover_color=COLOR_PALETTE["stop_button_hover"], state="disabled", font=ctk.CTkFont(weight="bold"))
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew", ipady=5)
        
        self.progress_label = ctk.CTkLabel(self, text="In attesa...", font=ctk.CTkFont(size=12), text_color=COLOR_PALETTE["text"])
        self.progress_label.grid(row=6, column=0, padx=20, pady=(0,5), sticky="w")
        self.progress_bar = ctk.CTkProgressBar(self, mode='determinate', progress_color=COLOR_PALETTE["accent_green"], fg_color=COLOR_PALETTE["secondary_button"])
        self.progress_bar.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.progress_bar.set(0)

        if initial_files:
            self.add_files_to_list(initial_files)
        
        self.update_command_preview()

    def time_str_to_seconds(self, time_str):
        """Converte una stringa di tempo HH:MM:SS.ms in secondi."""
        try:
            parts = time_str.split(':')
            h = int(parts[0])
            m = int(parts[1])
            s_parts = parts[2].split('.')
            s = int(s_parts[0])
            ms = int(s_parts[1]) if len(s_parts) > 1 else 0
            return h * 3600 + m * 60 + s + ms / 100.0
        except (ValueError, IndexError):
            return 0.0

    def run_ffmpeg_with_progress(self, command, file_index, total_files, filename):
        """Esegue un comando ffmpeg, parsando l'output per aggiornare la progress bar."""
        self.log(f"\n{'='*20}\nEsecuzione comando:\n{' '.join(shlex.quote(c) for c in command)}\n{'='*20}\n")
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.ffmpeg_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                startupinfo=startupinfo
            )

            duration_seconds = 0.0
            # Regex per trovare la durata e il tempo di avanzamento nell'output di ffmpeg
            duration_regex = re.compile(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})")
            progress_regex = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")

            for line in self.ffmpeg_process.stdout:
                if not self.is_running:
                    break
                self.log(line)

                # Cerca la durata totale del file
                if duration_seconds == 0:
                    duration_match = duration_regex.search(line)
                    if duration_match:
                        duration_seconds = self.time_str_to_seconds(duration_match.group(1))

                # Cerca il progresso attuale
                progress_match = progress_regex.search(line)
                if progress_match and duration_seconds > 0:
                    current_seconds = self.time_str_to_seconds(progress_match.group(1))
                    percentage = (current_seconds / duration_seconds)
                    
                    # Aggiorna label e progress bar
                    self.progress_label.configure(text=f"Processando File {file_index}/{total_files} ({percentage:.0%}): {filename}")
                    self.progress_bar.set(percentage)

            self.ffmpeg_process.wait()
            
            if self.is_running:
                if self.ffmpeg_process.returncode == 0:
                    self.log(f"\n--- File {filename} completato con successo. ---\n")
                else:
                    self.log(f"\n--- ERRORE: FFmpeg ha terminato con codice {self.ffmpeg_process.returncode} per il file {filename}. Controlla il log. ---\n")

        except Exception as e:
            self.log(f"Errore imprevisto durante l'elaborazione di {filename}: {e}\n")

    def process_queue(self, file_queue, is_manual):
        """Gestisce la coda di elaborazione dei file, sia in modalità manuale che automatica."""
        command_template = self.command_preview.get("1.0", tk.END).strip() if is_manual else None
        
        if is_manual and ("%%INPUT%%" not in command_template or "%%OUTPUT%%" not in command_template):
            self.log("ERRORE: Il template in modalità manuale deve contenere i segnaposto %%INPUT%% e %%OUTPUT%%.\n")
            self.toggle_ui_state(running=False)
            return

        total_files = len(file_queue)

        for i, input_filepath_str in enumerate(file_queue):
            if not self.is_running:
                break
            
            current_file_index = i + 1
            input_filepath = Path(input_filepath_str)
            output_filepath = self.generate_output_path(input_filepath)

            # Crea la cartella di output se non esiste
            output_filepath.parent.mkdir(parents=True, exist_ok=True)

            command = []
            if is_manual:
                concrete_command_str = command_template.replace("%%INPUT%%", f'"{input_filepath}"').replace("%%OUTPUT%%", f'"{output_filepath}"')
                
                # --- INIZIO DELLA CORREZIONE ---
                # shlex.split può corrompere i percorsi Windows. Per risolvere:
                # 1. Troviamo il percorso corretto e affidabile di ffmpeg.
                # 2. Dividiamo il comando manuale in una lista.
                # 3. Sostituiamo il primo elemento della lista (l'eseguibile, potenzialmente corrotto) con il percorso corretto.
                
                ffmpeg_path = self.find_ffmpeg()
                if not ffmpeg_path:
                    self.log(f"ERRORE: ffmpeg.exe non trovato per il file {input_filepath.name}.\n")
                    continue
                
                command_args = shlex.split(concrete_command_str)
                command_args[0] = ffmpeg_path # Sostituzione del percorso errato con quello corretto
                command = command_args
                # --- FINE DELLA CORREZIONE ---

            else:
                command = self.build_command(str(input_filepath))

            if not command:
                self.log(f"ERRORE: Impossibile generare il comando per {input_filepath.name}.\n")
                continue

            self.run_ffmpeg_with_progress(command, current_file_index, total_files, input_filepath.name)

        if self.is_running:
            self.log(f"\n--- Processo della coda ({'Manuale' if is_manual else 'Automatica'}) terminato. ---\n")
        else:
            self.log("\n--- Processo della coda interrotto dall'utente. ---\n")
            
        self.toggle_ui_state(running=False)


    def start_compression(self):
        file_queue = self.file_list_box.get("1.0", tk.END).strip().split("\n")
        file_queue = [f for f in file_queue if f]

        if not file_queue:
            self.log("ERRORE: Nessun file nella lista.\n")
            return
            
        self.is_running = True
        self.toggle_ui_state(running=True)
        
        is_manual_mode = self.manual_edit_switch.get() == 1
        
        thread = threading.Thread(target=self.process_queue, args=(file_queue, is_manual_mode), daemon=True)
        thread.start()

    def generate_output_path(self, input_path: Path) -> Path:
        """Genera il percorso del file di output usando pathlib."""
        codec = self.codec_var.get()

        if codec == "Crea proxy":
            proxy_dir = input_path.parent / "proxy"
            return proxy_dir / input_path.name
        else:
            cq_param = str(int(self.cq_slider.get()))
            new_name = f"{input_path.stem}_{codec}_CQ{cq_param}{input_path.suffix}"
            return input_path.parent / new_name

    def update_command_preview(self, force_template=False):
        if self.manual_edit_switch.get() == 1 and not force_template:
            return

        file_list = self.file_list_box.get("1.0", tk.END).strip().split("\n")
        file_list = [f for f in file_list if f]

        if not file_list:
            self.command_preview.configure(state="normal")
            self.command_preview.delete("1.0", tk.END)
            self.command_preview.insert("1.0", "Aggiungi uno o più file per vedere l'anteprima...")
            if not self.manual_edit_switch.get() == 1:
                self.command_preview.configure(state="disabled")
            return
        
        first_file = file_list[0]
        command_list = self.build_command(first_file)
        if not command_list: return
        
        if force_template:
            try:
                # Usa una rappresentazione Path per robustezza
                first_file_path = Path(first_file)
                output_path_str = str(self.generate_output_path(first_file_path))
                
                input_index = command_list.index(str(first_file_path))
                output_index = command_list.index(output_path_str)
                
                command_list[input_index] = "%%INPUT%%"
                command_list[output_index] = "%%OUTPUT%%"
            except ValueError:
                self.log("ERRORE: Impossibile creare il template del comando.\n")
                # Fallback sicuro: mostra il comando normale
                force_template = False
        
        # subprocess.list2cmdline è specifico per Windows e gestisce correttamente gli spazi
        preview_str = subprocess.list2cmdline(command_list)

        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert("1.0", preview_str)
        
        if not self.manual_edit_switch.get() == 1:
            self.command_preview.configure(state="disabled")

    # --- Metodi UI e di Utilità (in gran parte invariati) ---
    
    def toggle_wrap(self):
        """Alterna la modalità wrap della console"""
        if self.wrap_switch.get() == 1:
            self.output_console.configure(wrap="word")
        else:
            self.output_console.configure(wrap="none")
    
    def clear_console(self):
        """Pulisce il contenuto della console"""
        self.output_console.configure(state="normal")
        self.output_console.delete("1.0", tk.END)
        self.output_console.configure(state="disabled")

    def toggle_manual_edit_mode(self):
        is_manual_mode = self.manual_edit_switch.get() == 1
        
        if is_manual_mode:
            self.command_preview.configure(state="normal")
            self.codec_menu.configure(state="disabled")
            self.preset_menu.configure(state="disabled")
            self.cq_slider.configure(state="disabled")
            self.scale_menu.configure(state="disabled")
            self.start_button.configure(text="Avvia Coda Manuale")
            self.log("INFO: Modalità manuale attivata. Il comando verrà usato come template per tutti i file.\n"
                     "      Assicurati che i segnaposto %%INPUT%% e %%OUTPUT%% siano presenti.\n")
            self.update_command_preview(force_template=True)
        else:
            self.command_preview.configure(state="disabled")
            self.codec_menu.configure(state="normal")
            self.update_ui_for_codec(self.codec_var.get())
            self.start_button.configure(text="Avvia Compressione")
            self.log("INFO: Modalità manuale disattivata.\n")
            self.update_command_preview()

    def add_files_to_list(self, files):
        current_files_text = self.file_list_box.get("1.0", tk.END)
        for f in files:
            # Normalizza il percorso per evitare duplicati con slash diversi
            normalized_f = str(Path(f).resolve())
            if normalized_f not in current_files_text:
                self.file_list_box.insert(tk.END, normalized_f + "\n")
        self.update_command_preview()

    def clear_file_list(self):
        self.file_list_box.delete("1.0", tk.END)
        self.update_command_preview()
        
    def handle_drop(self, event):
        # l'evento data può contenere percorsi con parentesi graffe, che splitlist gestisce
        files = self.master.tk.splitlist(event.data)
        self.add_files_to_list(files)

    def browse_files(self):
        filepaths = filedialog.askopenfilenames()
        if filepaths: self.add_files_to_list(filepaths)

    def stop_compression(self):
        if self.is_running:
            self.is_running = False
            self.log("\n--- Richiesta di interruzione... Il processo si fermerà al termine del file corrente. ---\n")
            if self.ffmpeg_process:
                try:
                    # Invia 'q' a ffmpeg per un'uscita graceful
                    self.ffmpeg_process.stdin.write('q')
                    self.ffmpeg_process.stdin.flush()
                except (IOError, AttributeError, ProcessLookupError):
                     # Se lo stdin non è accessibile o il processo è già morto, termina forzatamente
                    try:
                        self.ffmpeg_process.terminate()
                    except ProcessLookupError:
                        pass

    def toggle_ui_state(self, running: bool):
        self.is_running = running
        state = "disabled" if running else "normal"
        
        self.start_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.manual_edit_switch.configure(state=state)
        self.stop_button.configure(state="normal" if running else "disabled")
        
        if not running:
            # Ripristina lo stato dei controlli in base alla modalità
            is_manual_mode = self.manual_edit_switch.get() == 1
            if is_manual_mode:
                self.toggle_manual_edit_mode() # Forza rilettura stato switch
            else:
                self.update_ui_for_codec(self.codec_var.get())
            
            self.progress_label.configure(text="Pronto.")
            self.progress_bar.set(0)

    def build_command(self, input_file):
        ffmpeg_path = self.find_ffmpeg()
        if not ffmpeg_path: 
            self.log("ERRORE: ffmpeg.exe non trovato. Assicurati sia nel PATH o nella cartella dell'app.\n")
            return None

        codec = self.codec_var.get()
        output_file = str(self.generate_output_path(Path(input_file)))
        
        if codec == 'Crea proxy':
            return [
                ffmpeg_path, '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', 
                '-i', input_file, '-c:v', 'av1_nvenc', '-vf', 'scale_cuda=-2:576', 
                '-preset', 'p1', '-cq', '0', '-tune', 'll', '-g', '30', '-c:a copy', output_file
            ]

        preset = self.preset_var.get()
        cq_param = str(int(self.cq_slider.get()))
        scale = self.scale_var.get()
        
        base_cmd = [ffmpeg_path, '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', input_file]
        video_opts = []

        scale_map = {"4k": "2160", "2k": "1440", "1080p": "1080", "720p": "720", "576p": "576", "480p": "480"}
        scale_height = scale_map.get(scale)

        codec_settings = {
            'AV1': {'c:v': 'av1_nvenc', 'rc:v': 'vbr'},
            'H265': {'c:v': 'hevc_nvenc', 'rc:v': 'vbr_hq'},
            'H264': {'c:v': 'h264_nvenc', 'rc:v': 'vbr_hq'}
        }
        
        if codec in codec_settings:
            settings = codec_settings[codec]
            video_opts.extend(['-c:v', settings['c:v'], '-preset', preset, '-rc', settings['rc:v'], '-cq', cq_param])
        
        if codec == 'AV1' and scale != "Nessuno" and scale_height:
            video_opts.extend(['-vf', f'scale_cuda=-2:{scale_height}'])
            
        video_opts.extend(['-tune', 'hq', '-rc-lookahead', '32', '-spatial-aq', '1', '-temporal-aq', '1', '-g', '30', '-bf', '2', '-movflags', '+faststart'])
        audio_opts = ['-c:a', 'copy']
        
        return base_cmd + video_opts + audio_opts + [output_file]

    def update_cq_label(self, value):
        self.cq_label.configure(text=f"{int(value)}")
        self.update_command_preview()

    def update_ui_for_codec(self, codec):
        is_proxy_mode = codec == "Crea proxy"
        controls_state = "disabled" if is_proxy_mode else "normal"
        
        self.preset_menu.configure(state=controls_state)
        self.cq_slider.configure(state=controls_state)
        
        if is_proxy_mode:
            self.scale_menu.configure(state="disabled")
            self.log("INFO: Modalità 'Crea proxy' selezionata. Le impostazioni sono fisse.\n")
        else:
            self.scale_menu.configure(state="normal" if codec == "AV1" else "disabled")
            if codec != "AV1":
                self.scale_menu.set("Nessuno")

        self.update_command_preview()

    def find_ffmpeg(self):
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        try:
            # Percorso per l'eseguibile PyInstaller
            base_path = sys._MEIPASS
        except AttributeError:
            # Percorso per l'esecuzione normale come script .py
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        local_path = os.path.join(base_path, 'ffmpeg.exe')
        if os.path.exists(local_path):
            return local_path
            
        return None

    def log(self, message):
        self.output_console.configure(state="normal")
        self.output_console.insert(tk.END, message)
        self.output_console.see(tk.END)
        self.output_console.configure(state="disabled")
        self.update_idletasks()
        
    def on_closing(self):
        if self.is_running:
            self.stop_compression()
        self.master.destroy()

# -----------------------------------------------------------------------------
# BLOCCO DI AVVIO DELL'APPLICAZIONE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Imposta la modalità di aspetto prima di creare qualsiasi finestra
    ctk.set_appearance_mode("Dark")
    
    # Crea la root window di TkinterDnD, che rimarrà nascosta
    hidden_root = TkinterDnD.Tk()
    hidden_root.withdraw() # Nascondi la finestra root

    # Crea la nostra finestra Toplevel personalizzata, che sarà l'interfaccia principale
    initial_files_from_args = sys.argv[1:]
    app_window = AppWindow(master=hidden_root, initial_files=initial_files_from_args)

    # Prova a impostare l'icona sulla finestra Tkinter sottostante
    def set_window_icon():
        try:
            app_window.wm_iconbitmap('icona.ico')
        except tk.TclError:
            print("Icona 'icona.ico' non trovata.")

    # Imposta l'icona dopo che la finestra è stata completamente creata
    app_window.after(100, set_window_icon)

    # Gestisci la chiusura: quando si chiude la AppWindow, si chiude anche la root nascosta
    def on_closing():
        app_window.on_closing() # Chiama il metodo di cleanup della nostra app
        hidden_root.destroy()   # Distrugge la root nascosta

    app_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Avvia il loop principale (sulla finestra nascosta, che gestirà gli eventi)
    hidden_root.mainloop()

