import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import subprocess
import threading
import os
import sys
import shutil
import shlex

from tkinterdnd2 import DND_FILES, TkinterDnD

# -----------------------------------------------------------------------------
# CLASSE PRINCIPALE - AppFrame
# -----------------------------------------------------------------------------

class AppFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.ffmpeg_process = None
        self.is_running = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=20, pady=(20,10), sticky="nsew")
        input_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(input_frame, text="File da Processare:").grid(row=0, column=0, columnspan=2, padx=10, pady=(5,0), sticky="w")
        self.file_list_box = ctk.CTkTextbox(input_frame, height=150, font=("Segoe UI", 13))
        self.file_list_box.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.file_list_box.drop_target_register(DND_FILES)
        self.file_list_box.dnd_bind('<<Drop>>', self.handle_drop)
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        button_frame.grid_columnconfigure((0,1), weight=1)
        self.browse_button = ctk.CTkButton(button_frame, text="Aggiungi File", command=self.browse_files)
        self.browse_button.grid(row=0, column=0, padx=(0,5), sticky="ew")
        self.clear_button = ctk.CTkButton(button_frame, text="Pulisci Lista", command=self.clear_file_list, fg_color="#555555", hover_color="#666666")
        self.clear_button.grid(row=0, column=1, padx=(5,0), sticky="ew")
        
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.options_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        ctk.CTkLabel(self.options_frame, text="Codec:", anchor="w").grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.codec_var = ctk.StringVar(value="AV1")
        self.codec_menu = ctk.CTkOptionMenu(self.options_frame, values=["AV1", "H265", "H264"], variable=self.codec_var, command=self.update_ui_for_codec)
        self.codec_menu.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.options_frame, text="Preset:", anchor="w").grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        self.preset_var = ctk.StringVar(value="p4")
        self.preset_menu = ctk.CTkOptionMenu(self.options_frame, values=["p1", "p2", "p3", "p4", "p5", "p6", "p7"], variable=self.preset_var, command=lambda _: self.update_command_preview())
        self.preset_menu.grid(row=1, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.options_frame, text="CQ (Qualità): 0-Auto, 1-maxQ, 51-minQ", anchor="w").grid(row=0, column=2, padx=20, pady=10, sticky="ew")
        self.cq_slider = ctk.CTkSlider(self.options_frame, from_=0, to=51, number_of_steps=52, command=self.update_cq_label)
        self.cq_slider.set(0)
        self.cq_slider.grid(row=1, column=2, padx=20, pady=5, sticky="ew")
        self.cq_label = ctk.CTkLabel(self.options_frame, text="0", font=ctk.CTkFont(size=14, weight="bold"))
        self.cq_label.grid(row=1, column=3, padx=10, pady=5)
        
        self.scaling_frame = ctk.CTkFrame(self)
        self.scaling_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.scaling_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.scaling_frame, text="Scaling Output:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.scale_var = ctk.StringVar(value="Nessuno")
        self.scale_menu = ctk.CTkOptionMenu(self.scaling_frame, values=["Nessuno", "1080p", "720p", "576p"], variable=self.scale_var, command=lambda _: self.update_command_preview())
        self.scale_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        preview_header_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
        preview_header_frame.pack(fill="x", padx=10, pady=(5,0))
        ctk.CTkLabel(preview_header_frame, text="Anteprima/Modifica Comando:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.manual_edit_switch = ctk.CTkSwitch(preview_header_frame, text="Modifica Manuale", command=self.toggle_manual_edit_mode)
        self.manual_edit_switch.pack(side="right")
        self.command_preview = ctk.CTkTextbox(preview_frame, height=100, wrap="word", font=("Courier New", 11), state="disabled")
        self.command_preview.pack(fill="x", expand=True, padx=10, pady=5)
        
        self.output_console = ctk.CTkTextbox(self, state="disabled", font=("Courier New", 11))
        self.output_console.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        self.start_button = ctk.CTkButton(action_frame, text="Avvia Compressione", command=self.start_compression)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.stop_button = ctk.CTkButton(action_frame, text="Ferma Compressione", command=self.stop_compression, fg_color="#D32F2F", hover_color="#B71C1C", state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.progress_label = ctk.CTkLabel(self, text="In attesa...", font=ctk.CTkFont(size=12))
        self.progress_label.grid(row=6, column=0, padx=20, pady=(0,5), sticky="w")
        self.progress_bar = ctk.CTkProgressBar(self, mode='determinate')
        self.progress_bar.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.progress_bar.set(0)
        
        self.update_command_preview()

    def toggle_manual_edit_mode(self):
        is_manual_mode = self.manual_edit_switch.get() == 1
        self.update_command_preview(force_template=is_manual_mode)
        
        if is_manual_mode:
            self.command_preview.configure(state="normal")
            self.codec_menu.configure(state="disabled")
            self.preset_menu.configure(state="disabled")
            self.cq_slider.configure(state="disabled")
            self.scale_menu.configure(state="disabled")
            self.start_button.configure(text="Avvia Coda Manuale")
            self.log("INFO: Modalità manuale attivata. Il comando verrà usato come template per tutti i file.\n"
                     "      Assicurati che i segnaposto %%INPUT%% e %%OUTPUT%% siano presenti.\n")
        else:
            self.command_preview.configure(state="disabled")
            self.codec_menu.configure(state="normal")
            self.preset_menu.configure(state="normal")
            self.cq_slider.configure(state="normal")
            self.scale_menu.configure(state="normal")
            self.start_button.configure(text="Avvia Compressione Coda")
            self.log("INFO: Modalità manuale disattivata.\n")

    def start_compression(self):
        # La "source of truth" è sempre il contenuto del textbox al momento del click
        file_queue = self.file_list_box.get("1.0", tk.END).strip().split("\n")
        file_queue = [f for f in file_queue if f]

        if not file_queue:
            self.log("ERRORE: Nessun file nella lista.\n")
            return
            
        self.is_running = True
        self.toggle_ui_state(running=True)
        
        if self.manual_edit_switch.get() == 1:
            thread = threading.Thread(target=self.process_manual_queue, args=(file_queue,), daemon=True)
        else:
            thread = threading.Thread(target=self.process_auto_queue, args=(file_queue,), daemon=True)
        
        thread.start()

    def process_manual_queue(self, file_queue):
        command_template = self.command_preview.get("1.0", tk.END).strip()
        
        if "%%INPUT%%" not in command_template or "%%OUTPUT%%" not in command_template:
            self.log("ERRORE: Il template in modalità manuale deve contenere i segnaposto %%INPUT%% e %%OUTPUT%%.\n")
            self.toggle_ui_state(running=False)
            return

        total_files = len(file_queue)
        self.progress_bar.configure(mode="determinate")

        for i, input_filepath in enumerate(file_queue):
            if not self.is_running: break
            self.progress_label.configure(text=f"Processando file {i+1} di {total_files}: {os.path.basename(input_filepath)}")
            output_filepath = self.generate_manual_output_path(input_filepath)
            concrete_command_str = command_template.replace("%%INPUT%%", f'"{input_filepath}"').replace("%%OUTPUT%%", f'"{output_filepath}"')
            self.log(f"\n{'='*20}\nEsecuzione per {input_filepath}:\n{concrete_command_str}\n{'='*20}\n")
            
            try:
                command_list = shlex.split(concrete_command_str)
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self.ffmpeg_process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', startupinfo=startupinfo)
                for line in self.ffmpeg_process.stdout: self.log(line.strip() + "\r")
                self.ffmpeg_process.wait()
            except Exception as e:
                self.log(f"Errore imprevisto durante l'elaborazione di {input_filepath}: {e}\n")

            if not self.is_running: break
            progress = (i + 1) / total_files
            self.progress_bar.set(progress)

        self.log("\n--- Processo della coda manuale terminato. ---\n")
        self.toggle_ui_state(running=False)

    def process_auto_queue(self, file_queue):
        total_files = len(file_queue)
        self.progress_bar.configure(mode="determinate")
        for i, filepath in enumerate(file_queue):
            if not self.is_running: break
            self.progress_label.configure(text=f"Processando file {i+1} di {total_files}: {os.path.basename(filepath)}")
            self.log(f"\n{'='*20}\nInizio elaborazione file {i+1}/{total_files}: {filepath}\n{'='*20}\n")
            command = self.build_command(filepath)
            if not command: continue
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self.ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', startupinfo=startupinfo)
                for line in self.ffmpeg_process.stdout: self.log(line.strip() + "\r")
                self.ffmpeg_process.wait()
            except Exception as e: self.log(f"Errore imprevisto: {e}\n")
            if not self.is_running: break
            progress = (i + 1) / total_files
            self.progress_bar.set(progress)
        self.log("\n--- Processo della coda terminato. ---\n")
        self.toggle_ui_state(running=False)

    def generate_manual_output_path(self, input_path):
        codec = self.codec_var.get()
        base, ext = os.path.splitext(input_path)
        return f"{base}_converted_{codec}{ext}"

    def update_command_preview(self, force_template=False):
        if self.manual_edit_switch.get() == 1 and not force_template:
            return

        # Legge la lista di file direttamente dal textbox
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
        
        # Se stiamo forzando la creazione del template...
        if force_template:
            # 1. Trova l'indice dell'input file e dell'output file nella lista
            try:
                input_index = command_list.index(first_file)
                output_index = len(command_list) - 1 # L'output è sempre l'ultimo
                
                # 2. Sostituisci gli elementi nella lista con i segnaposto
                command_list[input_index] = "%%INPUT%%"
                command_list[output_index] = "%%OUTPUT%%"
            except ValueError:
                self.log("ERRORE: Impossibile creare il template del comando.\n")
                return
        
        # 3. Genera la stringa di anteprima dalla lista (modificata o originale)
        preview_str = subprocess.list2cmdline(command_list)

        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert("1.0", preview_str)
        
        if not self.manual_edit_switch.get() == 1:
            self.command_preview.configure(state="disabled")

    def add_files_to_list(self, files):
        current_files_text = self.file_list_box.get("1.0", tk.END)
        self.file_list_box.configure(state="normal")
        for f in files:
            # Aggiunge solo se non già presente nel testo
            if f not in current_files_text:
                self.file_list_box.insert(tk.END, f + "\n")
        self.file_list_box.configure(state="disabled")
        self.update_command_preview()

    def clear_file_list(self):
        self.file_list_box.configure(state="normal")
        self.file_list_box.delete("1.0", tk.END)
        self.file_list_box.configure(state="disabled")
        self.update_command_preview()
        
    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        self.add_files_to_list(files)

    def browse_files(self):
        filepaths = filedialog.askopenfilenames()
        if filepaths: self.add_files_to_list(filepaths)

    def stop_compression(self):
        self.is_running = False
        if self.ffmpeg_process:
            self.log("\n--- Richiesta di interruzione... ---")
            self.ffmpeg_process.terminate()
        self.log("\n--- La coda verrà interrotta dopo il file corrente. ---\n")

    def toggle_ui_state(self, running: bool):
        self.is_running = running
        state = "disabled" if running else "normal"
        self.start_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.manual_edit_switch.configure(state=state)

        if not running and self.manual_edit_switch.get() == 1:
            self.toggle_manual_edit_mode()
        
        self.stop_button.configure(state="normal" if running else "disabled")
        if not running:
             self.progress_label.configure(text="Pronto.")
             self.progress_bar.set(0)

    def build_command(self, input_file):
        ffmpeg_path = self.find_ffmpeg()
        if not ffmpeg_path: 
            self.log("ERRORE: ffmpeg.exe non trovato. Assicurati sia nel PATH o nella cartella dell'app.\n")
            return None

        codec = self.codec_var.get()
        preset = self.preset_var.get()
        cq_param = str(int(self.cq_slider.get()))
        scale = self.scale_var.get()
        input_dir, input_filename = os.path.split(input_file)
        filename_base, file_ext = os.path.splitext(input_filename)
        output_filename = os.path.join(input_dir, f"{filename_base}_{codec}_CQ{cq_param}{file_ext}")
        
        base_cmd = ['ffmpeg.exe', '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', input_file]
        video_opts = []

        if codec == 'AV1':
            video_opts = ['-c:v', 'av1_nvenc', '-preset', preset, '-rc:v', 'vbr', '-cq:v', cq_param]
            if scale != "Nessuno": video_opts.extend(['-vf', f'scale_cuda=-2:{scale.replace("p","")}'])
        elif codec == 'H265':
            video_opts = ['-c:v', 'hevc_nvenc', '-preset', preset, '-rc:v', 'vbr_hq', '-cq:v', cq_param]
        elif codec == 'H264':
            video_opts = ['-c:v', 'h264_nvenc', '-preset', preset, '-rc:v', 'vbr_hq', '-cq:v', cq_param]
            
        video_opts.extend(['-rc-lookahead', '32', '-spatial-aq', '1', '-temporal-aq', '1'])
        audio_opts = ['-c:a', 'copy']
        output_opts = [output_filename]
        return base_cmd + video_opts + audio_opts + output_opts

    def update_cq_label(self, value):
        self.cq_label.configure(text=f"{int(value)}")
        self.update_command_preview()

    def update_ui_for_codec(self, codec):
        if codec == "AV1": self.scale_menu.configure(state="normal")
        else:
            self.scale_menu.set("Nessuno")
            self.scale_menu.configure(state="disabled")
        self.update_command_preview()

    def find_ffmpeg(self):
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path: return ffmpeg_path
        local_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'ffmpeg.exe')
        if os.path.exists(local_path): return local_path
        return None

    def log(self, message):
        self.output_console.configure(state="normal")
        self.output_console.insert(tk.END, message)
        self.output_console.see(tk.END)
        self.output_console.configure(state="disabled")
        self.update_idletasks()
        
    def on_closing(self):
        self.is_running = False
        if self.ffmpeg_process: self.stop_compression()
        self.master.destroy()

# -----------------------------------------------------------------------------
# BLOCCO DI AVVIO DELL'APPLICAZIONE (Invariato)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    root.configure(bg="#242424")
    root.title("FFmpeg GUI")
    root.geometry("900x900")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    app_frame = AppFrame(master=root)
    app_frame.grid(row=0, column=0, sticky="nsew")
    root.protocol("WM_DELETE_WINDOW", app_frame.on_closing)
    root.mainloop()