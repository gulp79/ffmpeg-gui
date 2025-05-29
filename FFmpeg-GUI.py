import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import subprocess
import threading
import os
import sys
import shutil

# Importato per il Drag & Drop
from tkinterdnd2 import DND_FILES, TkinterDnD

# -----------------------------------------------------------------------------
# CLASSE PRINCIPALE - Ora è un CTkFrame, non più la finestra intera.
# Questo la rende un "componente" che possiamo inserire in qualsiasi finestra.
# -----------------------------------------------------------------------------
class AppFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master # Salva un riferimento alla finestra principale
        self.ffmpeg_process = None

        # Configurazione del layout a griglia (per il frame stesso)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # --- Frame Principale ---
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)

        # 1. Selezione File Input (con Drag & Drop abilitato)
        ctk.CTkLabel(main_frame, text="File di Input:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.input_entry = ctk.CTkEntry(main_frame, placeholder_text="Trascina un file qui o clicca 'Sfoglia'")
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Abilitazione del Drag & Drop - Ora funzionerà perché il master è una finestra DND
        self.input_entry.drop_target_register(DND_FILES)
        self.input_entry.dnd_bind('<<Drop>>', self.handle_drop)
        self.input_entry.bind("<KeyRelease>", lambda event: self.update_command_preview())

        self.browse_button = ctk.CTkButton(main_frame, text="Sfoglia", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

        options_frame = ctk.CTkFrame(self)
        options_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        options_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        ctk.CTkLabel(options_frame, text="Codec:", anchor="w").grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.codec_var = ctk.StringVar(value="AV1")
        self.codec_menu = ctk.CTkOptionMenu(options_frame, values=["AV1", "H265", "H264"], variable=self.codec_var, command=self.update_ui_for_codec)
        self.codec_menu.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="Preset:", anchor="w").grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        self.preset_var = ctk.StringVar(value="p4")
        self.preset_menu = ctk.CTkOptionMenu(options_frame, values=["p1", "p2", "p3", "p4", "p5", "p6", "p7"], variable=self.preset_var, command=lambda _: self.update_command_preview())
        self.preset_menu.grid(row=1, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(options_frame, text="CQ (Qualità - 0 auto, 1 max, 51 min):", anchor="w").grid(row=0, column=2, padx=20, pady=10, sticky="ew")
        self.cq_slider = ctk.CTkSlider(options_frame, from_=0, to=51, number_of_steps=52, command=self.update_cq_label)
        self.cq_slider.set(0)
        self.cq_slider.grid(row=1, column=2, padx=20, pady=5, sticky="ew")
        self.cq_label = ctk.CTkLabel(options_frame, text="0", font=ctk.CTkFont(size=14, weight="bold"))
        self.cq_label.grid(row=1, column=3, padx=10, pady=5)
        
        scaling_frame = ctk.CTkFrame(self)
        scaling_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        scaling_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(scaling_frame, text="Scaling Output:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.scale_var = ctk.StringVar(value="Nessuno")
        self.scale_menu = ctk.CTkOptionMenu(scaling_frame, values=["Nessuno", "1080p", "720p", "576p"], variable=self.scale_var, command=lambda _: self.update_command_preview())
        self.scale_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")
        ctk.CTkLabel(preview_frame, text="Anteprima Comando FFmpeg:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        self.command_preview = ctk.CTkTextbox(preview_frame, height=80, state="disabled", wrap="word", font=("Courier New", 11))
        self.command_preview.pack(fill="x", expand=True, padx=10, pady=5)
        
        self.output_console = ctk.CTkTextbox(self, state="disabled", font=("Courier New", 11))
        self.output_console.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        
        self.start_button = ctk.CTkButton(action_frame, text="Avvia Compressione", command=self.start_compression)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(action_frame, text="Ferma Compressione", command=self.stop_compression, fg_color="#D32F2F", hover_color="#B71C1C")
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.stop_button.configure(state="disabled")

        self.progress_bar = ctk.CTkProgressBar(self, mode='indeterminate')
        self.progress_bar.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.progress_bar.set(0)
        
        self.update_command_preview()

    # (Tutte le funzioni logiche da qui in poi sono identiche a prima)
    # ...
    def handle_drop(self, event):
        filepath = self.tk.splitlist(event.data)[0]
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, filepath)
        self.update_command_preview()

    def browse_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filepath)
            self.update_command_preview()

    def update_cq_label(self, value):
        self.cq_label.configure(text=f"{int(value)}")
        self.update_command_preview()

    def update_ui_for_codec(self, codec):
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
        local_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'ffmpeg.exe')
        if os.path.exists(local_path):
            return local_path
        return None

    def build_command(self):
        ffmpeg_path = self.find_ffmpeg()
        if not ffmpeg_path:
            self.log("ERRORE: Impossibile trovare ffmpeg.exe.\n")
            return None
        input_file = self.input_entry.get()
        if not input_file:
            return None
        codec = self.codec_var.get()
        preset = self.preset_var.get()
        cq_param = str(int(self.cq_slider.get()))
        scale = self.scale_var.get()
        input_dir, input_filename = os.path.split(input_file)
        filename_base, file_ext = os.path.splitext(input_filename)
        output_filename = os.path.join(input_dir, f"{filename_base}_{codec}_CQ{cq_param}{file_ext}")
        base_cmd = [ffmpeg_path, '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', input_file]
        video_opts = []
        if codec == 'AV1':
            video_opts = ['-c:v', 'av1_nvenc', '-preset', preset, '-rc:v', 'vbr', '-cq:v', cq_param]
            if scale != "Nessuno":
                height = scale.replace('p', '')
                video_opts.extend(['-vf', f'scale_cuda=-2:{height}'])
        elif codec == 'H265':
            video_opts = ['-c:v', 'hevc_nvenc', '-preset', preset, '-rc:v', 'vbr_hq', '-cq:v', cq_param]
        elif codec == 'H264':
            video_opts = ['-c:v', 'h264_nvenc', '-preset', preset, '-rc:v', 'vbr_hq', '-cq:v', cq_param]
        video_opts.extend(['-rc-lookahead', '32', '-spatial-aq', '1', '-temporal-aq', '1'])
        audio_opts = ['-c:a', 'copy']
        output_opts = [output_filename]
        return base_cmd + video_opts + audio_opts + output_opts

    def update_command_preview(self):
        command_list = self.build_command()
        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        if command_list:
            preview_str = subprocess.list2cmdline(command_list)
            self.command_preview.insert("1.0", preview_str)
        else:
            self.command_preview.insert("1.0", "Completa le opzioni per vedere l'anteprima del comando...")
        self.command_preview.configure(state="disabled")

    def start_compression(self):
        command_list = self.build_command()
        if not command_list:
            self.log("ERRORE: Il comando non può essere costruito.\n")
            return
        self.log(f"Comando Eseguito:\n{subprocess.list2cmdline(command_list)}\n\n")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress_bar.start()
        thread = threading.Thread(target=self.run_ffmpeg, args=(command_list,), daemon=True)
        thread.start()

    def stop_compression(self):
        if self.ffmpeg_process:
            self.log("\n--- Richiesta di interruzione... ---")
            self.ffmpeg_process.terminate()
            self.ffmpeg_process = None
            self.reset_ui()

    def run_ffmpeg(self, command):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', startupinfo=startupinfo)
            for line in self.ffmpeg_process.stdout:
                self.log(line)
            self.ffmpeg_process.wait()
            if self.ffmpeg_process and self.ffmpeg_process.returncode == 0:
                self.log("\n--- Compressione completata con successo! ---")
            elif self.ffmpeg_process:
                self.log(f"\n--- Compressione terminata con codice di errore: {self.ffmpeg_process.returncode} ---")
        except FileNotFoundError:
            self.log(f"\nERRORE FATALE: Impossibile trovare l'eseguibile '{command[0]}'.\n")
        except Exception as e:
            self.log(f"\nErrore durante l'esecuzione di FFmpeg: {e}")
        finally:
            self.ffmpeg_process = None
            self.reset_ui()

    def log(self, message):
        self.output_console.configure(state="normal")
        self.output_console.insert(tk.END, message)
        self.output_console.see(tk.END)
        self.output_console.configure(state="disabled")
        self.update_idletasks()

    def reset_ui(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.progress_bar.stop()
        self.progress_bar.set(0)

    def on_closing(self):
        if self.ffmpeg_process:
            self.stop_compression()
        self.master.destroy() # Chiude la finestra principale


# -----------------------------------------------------------------------------
# NUOVO BLOCCO DI AVVIO CORRETTO
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Crea la finestra principale come una finestra TkinterDnD.
    root = TkinterDnD.Tk()
    
    # 2. Imposta i temi e le proprietà della finestra principale
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # --- INIZIO MODIFICA ---
    # Imposta il colore di sfondo della finestra root perché corrisponda al tema scuro
    # Il colore #242424 è quello standard del tema scuro di CustomTkinter
    root.configure(bg="#242424")
    # --- FINE MODIFICA ---

    root.title("FFmpeg GUI Moderna")
    root.geometry("850x850")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # 3. Crea un'istanza del nostro frame applicativo e la inserisce nella finestra
    # NOTA: Rimuoviamo il padding qui, perché il frame interno ha già il suo.
    app_frame = AppFrame(master=root)
    app_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew") # padx e pady a 0

    # 4. Imposta il comportamento alla chiusura
    root.protocol("WM_DELETE_WINDOW", app_frame.on_closing)

    # 5. Avvia il loop principale
    root.mainloop()