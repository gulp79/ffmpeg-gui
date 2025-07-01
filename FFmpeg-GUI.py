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

class AppFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_PALETTE["app_bg"])
        self.master = master
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
        self.preset_var = ctk.StringVar(value="p4")
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
        self.command_preview = ctk.CTkTextbox(preview_frame, height=100, wrap="word", font=("Courier New", 11), state="disabled", fg_color=COLOR_PALETTE["textbox_bg"], text_color=COLOR_PALETTE["text"], border_width=0)
        self.command_preview.pack(fill="x", expand=True, padx=10, pady=5)
        
        # --- Console di Output e Azioni ---
        self.output_console = ctk.CTkTextbox(self, state="disabled", font=("Courier New", 11), fg_color=COLOR_PALETTE["textbox_bg"], text_color=COLOR_PALETTE["text"], border_width=0)
        self.output_console.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        
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
            self.update_ui_for_codec(self.codec_var.get())
            self.start_button.configure(text="Avvia Compressione Coda")
            self.log("INFO: Modalità manuale disattivata.\n")

    def start_compression(self):
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
            output_filepath = self.generate_output_path(input_filepath)
            
            output_dir = os.path.dirname(output_filepath)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

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
            
            output_filepath = command[-1]
            output_dir = os.path.dirname(output_filepath)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
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

    def generate_output_path(self, input_path):
        codec = self.codec_var.get()
        input_dir, input_filename = os.path.split(input_path)
        filename_base, file_ext = os.path.splitext(input_filename)

        if codec == "Crea proxy":
            proxy_dir = os.path.join(input_dir, "proxy")
            return os.path.join(proxy_dir, input_filename)
        else:
            cq_param = str(int(self.cq_slider.get()))
            return os.path.join(input_dir, f"{filename_base}_{codec}_CQ{cq_param}{file_ext}")

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
                input_index = command_list.index(first_file)
                output_index = len(command_list) - 1 
                
                command_list[input_index] = "%%INPUT%%"
                command_list[output_index] = "%%OUTPUT%%"
            except ValueError:
                self.log("ERRORE: Impossibile creare il template del comando.\n")
                return
        
        preview_str = subprocess.list2cmdline(command_list)

        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert("1.0", preview_str)
        
        if not self.manual_edit_switch.get() == 1:
            self.command_preview.configure(state="disabled")

    def add_files_to_list(self, files):
        current_files_text = self.file_list_box.get("1.0", tk.END)
        for f in files:
            if f not in current_files_text:
                self.file_list_box.insert(tk.END, f + "\n")
        self.update_command_preview()

    def clear_file_list(self):
        self.file_list_box.delete("1.0", tk.END)
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
            try:
                self.ffmpeg_process.terminate()
            except ProcessLookupError:
                pass
        self.log("\n--- La coda verrà interrotta dopo il file corrente. ---\n")

    def toggle_ui_state(self, running: bool):
        self.is_running = running
        state = "disabled" if running else "normal"
        
        self.start_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.manual_edit_switch.configure(state=state)
        self.stop_button.configure(state="normal" if running else "disabled")
        
        if not running and self.manual_edit_switch.get() == 0:
            self.update_ui_for_codec(self.codec_var.get())
        
        if not running:
             self.progress_label.configure(text="Pronto.")
             self.progress_bar.set(0)

    def build_command(self, input_file):
        ffmpeg_path = self.find_ffmpeg()
        if not ffmpeg_path: 
            self.log("ERRORE: ffmpeg.exe non trovato. Assicurati sia nel PATH o nella cartella dell'app.\n")
            return None

        codec = self.codec_var.get()
        
        if codec == 'Crea proxy':
            output_file = self.generate_output_path(input_file)
            return [
                ffmpeg_path, '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', 
                '-i', input_file, '-c:v', 'av1_nvenc', '-vf', 'scale_cuda=-2:576', 
                '-preset', 'p1', '-cq:v', '0', '-tune', 'll', '-an', output_file
            ]

        preset = self.preset_var.get()
        cq_param = str(int(self.cq_slider.get()))
        scale = self.scale_var.get()
        output_filename = self.generate_output_path(input_file)
        
        base_cmd = [ffmpeg_path, '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', input_file]
        video_opts = []

        scale_map = {"4k": "2160", "2k": "1440", "1080p": "1080", "720p": "720", "576p": "576", "480p": "480"}
        scale_height = scale_map.get(scale)

        # Costruzione dinamica del comando
        codec_settings = {
            'AV1': {'c:v': 'av1_nvenc', 'rc:v': 'vbr'},
            'H265': {'c:v': 'hevc_nvenc', 'rc:v': 'vbr_hq'},
            'H264': {'c:v': 'h264_nvenc', 'rc:v': 'vbr_hq'}
        }
        
        if codec in codec_settings:
            settings = codec_settings[codec]
            video_opts.extend(['-c:v', settings['c:v'], '-preset', preset, '-rc:v', settings['rc:v'], '-cq:v', cq_param])
        
        if codec == 'AV1' and scale != "Nessuno" and scale_height:
            video_opts.extend(['-vf', f'scale_cuda=-2:{scale_height}'])
            
        video_opts.extend(['-rc-lookahead', '32', '-spatial-aq', '1', '-temporal-aq', '1'])
        audio_opts = ['-c:a', 'copy']
        output_opts = [output_filename]
        
        return base_cmd + video_opts + audio_opts + output_opts


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
            if codec == "AV1":
                self.scale_menu.configure(state="normal")
            else:
                self.scale_menu.set("Nessuno")
                self.scale_menu.configure(state="disabled")

        self.update_command_preview()

    def find_ffmpeg(self):
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        try:
            base_path = sys._MEIPASS
        except AttributeError:
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
        self.is_running = False
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            self.stop_compression()
        self.master.destroy()

# -----------------------------------------------------------------------------
# BLOCCO DI AVVIO DELL'APPLICAZIONE (CORRETTO)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Usa TkinterDnD.Tk() come root window per il drag-and-drop
    root = TkinterDnD.Tk() 
    ctk.set_appearance_mode("Dark")
    
    root.title("FFmpeg GUI")
    root.geometry("900x900")
    
    # La riga "root.configure(fg_color=...)" è stata rimossa.
    # Il colore di sfondo è già gestito dal frame AppFrame,
    # che riempie l'intera finestra.
    
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    app_frame = AppFrame(master=root)
    app_frame.grid(row=0, column=0, sticky="nsew") # Rimosso padx/pady per un riempimento completo
    
    root.protocol("WM_DELETE_WINDOW", app_frame.on_closing)
    root.mainloop()
