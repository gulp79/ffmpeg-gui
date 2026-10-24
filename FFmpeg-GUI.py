import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import subprocess
import threading
import os
import sys
import shutil
import shlex
import re
import platform
from pathlib import Path

from tkinterdnd2 import DND_FILES, TkinterDnD

import presets_manager
import command_builder

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
        
        # --- IMPOSTAZIONI FINESTRA (spostate qui) ---
        self.title("FFmpeg GUI")
        self.geometry("900x900")
        
        # Configura il layout della griglia direttamente sulla finestra
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.ffmpeg_process = None
        self.is_running = False

        # Carica i preset esterni
        self.presets_data, load_error = presets_manager.load_presets()
        # Preset corrente (aggiornato da update_video_ui_from_preset)
        self.current_preset_config = {}
        
        # Variabili modalità
        self.mode_var = ctk.StringVar(value="Video")
        
        # Variabili Video
        self.codec_var = ctk.StringVar(value="")
        self.preset_var = ctk.StringVar(value="")
        self.scale_var = ctk.StringVar(value="Nessuno")
        
        # Variabili Animazioni (con default dal JSON)
        anim_defaults = self.presets_data.get("animation_presets", {}).get("defaults", {})
        self.anim_format_var = ctk.StringVar(value="WebP")
        self.anim_fps_var = ctk.DoubleVar(value=float(anim_defaults.get("fps", 15)))
        self.anim_width_var = ctk.StringVar(value=str(anim_defaults.get("target_width", 1920)))
        self.anim_custom_width_var = ctk.StringVar(value="1920")
        
        self.webp_quality_var = ctk.DoubleVar(value=float(anim_defaults.get("webp_quality", 70)))
        self.webp_method_var = ctk.StringVar(value=str(anim_defaults.get("webp_method", 6)))
        
        self.avif_crf_var = ctk.DoubleVar(value=float(anim_defaults.get("avif_crf", 32)))
        self.avif_preset_var = ctk.StringVar(value=str(anim_defaults.get("avif_preset", 6)))
        self.avif_encoder_var = ctk.StringVar(value=anim_defaults.get("avif_encoder", "libsvtav1"))
        
        self.gif_colors_var = ctk.DoubleVar(value=float(anim_defaults.get("gif_colors", 64)))
        self.gif_dither_var = ctk.StringVar(value=anim_defaults.get("gif_dither", "bayer:bayer_scale=3"))
        self.gif_optimize_var = ctk.BooleanVar(value=True)
        
        # Aggiorna l'anteprima se cambia il valore della larghezza custom
        self.anim_custom_width_var.trace_add("write", lambda *args: self.update_command_preview())

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
        
        # --- Commutatore Modalità (Row 1) ---
        self.mode_selector = ctk.CTkSegmentedButton(self, values=["Video", "Animazioni"], variable=self.mode_var, command=self.on_mode_change, fg_color=COLOR_PALETTE["frame_bg"], selected_color=COLOR_PALETTE["accent_green"], selected_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text"], text_color_disabled=COLOR_PALETTE["secondary_button"])
        self.mode_selector.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")

        # --- Frame Opzioni Video (Row 2, Visibile di Default) ---
        self.video_options_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"])
        self.video_options_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        video_preset_names = [p["name"] for p in self.presets_data.get("video_presets", [])]
        if video_preset_names:
            self.codec_var.set(video_preset_names[0])
            
        ctk.CTkLabel(self.video_options_frame, text="Codec Video:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, padx=20, pady=(10,0), sticky="ew")
        self.codec_menu = ctk.CTkOptionMenu(self.video_options_frame, values=video_preset_names, variable=self.codec_var, command=lambda _: self.update_video_ui_from_preset(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.codec_menu.grid(row=1, column=0, padx=20, pady=(5,10), sticky="ew")

        ctk.CTkLabel(self.video_options_frame, text="Preset Velocità:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=1, padx=20, pady=(10,0), sticky="ew")
        self.preset_menu = ctk.CTkOptionMenu(self.video_options_frame, values=["p1", "p2", "p3", "p4", "p5", "p6", "p7"], variable=self.preset_var, command=lambda _: self.update_command_preview(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.preset_menu.grid(row=1, column=1, padx=20, pady=(5,10), sticky="ew")

        self.cq_title_label = ctk.CTkLabel(self.video_options_frame, text="CQ (Qualità):", anchor="w", text_color=COLOR_PALETTE["text"])
        self.cq_title_label.grid(row=0, column=2, padx=20, pady=(10,0), sticky="ew")
        self.cq_slider = ctk.CTkSlider(self.video_options_frame, from_=0, to=51, number_of_steps=52, command=self.update_cq_label, button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], progress_color=COLOR_PALETTE["accent_green"])
        self.cq_slider.grid(row=1, column=2, padx=20, pady=(5,10), sticky="ew")
        self.cq_label = ctk.CTkLabel(self.video_options_frame, text="0", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_PALETTE["accent_green"])
        self.cq_label.grid(row=1, column=3, padx=10, pady=(5,10))

        # Scaling
        ctk.CTkLabel(self.video_options_frame, text="Ridimensionamento:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=2, column=0, padx=20, pady=(5,0), sticky="ew")
        self.scale_menu = ctk.CTkOptionMenu(self.video_options_frame, values=["Nessuno", "4k", "2k", "1080p", "720p", "576p", "480p"], variable=self.scale_var, command=lambda _: self.update_command_preview(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.scale_menu.grid(row=3, column=0, columnspan=2, padx=20, pady=(5,10), sticky="ew")
        
        self.video_options_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # --- Frame Opzioni Animazioni (Row 2, Nascosto di Default) ---
        self.anim_options_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"])
        self.anim_options_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Row 0: Labels
        ctk.CTkLabel(self.anim_options_frame, text="Formato:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, padx=15, pady=(10,0), sticky="ew")
        self.fps_title_label = ctk.CTkLabel(self.anim_options_frame, text=f"FPS ({int(self.anim_fps_var.get())}):", anchor="w", text_color=COLOR_PALETTE["text"])
        self.fps_title_label.grid(row=0, column=1, padx=15, pady=(10,0), sticky="ew")
        ctk.CTkLabel(self.anim_options_frame, text="Larghezza Max:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=2, padx=15, pady=(10,0), sticky="ew")
        self.custom_width_title_label = ctk.CTkLabel(self.anim_options_frame, text="Larghezza Custom (px):", anchor="w", text_color=COLOR_PALETTE["text"])
        
        # Row 1: Menus/Sliders
        self.anim_format_menu = ctk.CTkOptionMenu(self.anim_options_frame, values=["WebP", "AVIF", "GIF"], variable=self.anim_format_var, command=lambda _: self.update_anim_ui_from_format(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.anim_format_menu.grid(row=1, column=0, padx=15, pady=(5,10), sticky="ew")
        
        self.anim_fps_slider = ctk.CTkSlider(self.anim_options_frame, from_=1, to=60, number_of_steps=59, variable=self.anim_fps_var, command=self.update_fps_label, button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], progress_color=COLOR_PALETTE["accent_green"])
        self.anim_fps_slider.grid(row=1, column=1, padx=15, pady=(5,10), sticky="ew")
        
        width_options_list = [str(w) for w in anim_defaults.get("width_options", [1920, 1280, 720])] + ["Custom"]
        self.anim_width_menu = ctk.CTkOptionMenu(self.anim_options_frame, values=width_options_list, variable=self.anim_width_var, command=lambda _: self.update_custom_width_visibility(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.anim_width_menu.grid(row=1, column=2, padx=15, pady=(5,10), sticky="ew")
        
        self.custom_width_entry = ctk.CTkEntry(self.anim_options_frame, textvariable=self.anim_custom_width_var, fg_color=COLOR_PALETTE["textbox_bg"], text_color=COLOR_PALETTE["text"], border_width=1, border_color=COLOR_PALETTE["secondary_button"])
        
        # Row 2: Dettagli Formato
        self.anim_details_frame = ctk.CTkFrame(self.anim_options_frame, fg_color="transparent")
        self.anim_details_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
        self.anim_details_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # WebP
        self.webp_details_frame = ctk.CTkFrame(self.anim_details_frame, fg_color="transparent")
        self.webp_details_frame.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(self.webp_details_frame, text="Qualità WebP:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.webp_q_slider = ctk.CTkSlider(self.webp_details_frame, from_=0, to=100, number_of_steps=101, variable=self.webp_quality_var, command=self.webp_q_slider_callback, button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], progress_color=COLOR_PALETTE["accent_green"])
        self.webp_q_slider.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.webp_q_label = ctk.CTkLabel(self.webp_details_frame, text=str(int(self.webp_quality_var.get())), font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_PALETTE["accent_green"])
        self.webp_q_label.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkLabel(self.webp_details_frame, text="Compressione (0-6):", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        self.webp_method_menu = ctk.CTkOptionMenu(self.webp_details_frame, values=["0", "1", "2", "3", "4", "5", "6"], variable=self.webp_method_var, command=lambda _: self.update_command_preview(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.webp_method_menu.grid(row=1, column=2, padx=10, pady=5, sticky="ew")
        
        # AVIF
        self.avif_details_frame = ctk.CTkFrame(self.anim_details_frame, fg_color="transparent")
        self.avif_details_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(self.avif_details_frame, text="CRF AVIF (Qualità):", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.avif_crf_slider = ctk.CTkSlider(self.avif_details_frame, from_=0, to=63, number_of_steps=64, variable=self.avif_crf_var, command=self.avif_crf_slider_callback, button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], progress_color=COLOR_PALETTE["accent_green"])
        self.avif_crf_slider.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.avif_crf_label = ctk.CTkLabel(self.avif_details_frame, text=str(int(self.avif_crf_var.get())), font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_PALETTE["accent_green"])
        self.avif_crf_label.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkLabel(self.avif_details_frame, text="Preset AVIF (Velocità):", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        self.avif_preset_menu = ctk.CTkOptionMenu(self.avif_details_frame, values=[str(x) for x in range(14)], variable=self.avif_preset_var, command=lambda _: self.update_command_preview(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.avif_preset_menu.grid(row=1, column=2, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.avif_details_frame, text="Encoder AVIF:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        self.avif_enc_menu = ctk.CTkOptionMenu(self.avif_details_frame, values=["libsvtav1", "libaom-av1"], variable=self.avif_encoder_var, command=self.on_avif_encoder_change, fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.avif_enc_menu.grid(row=1, column=3, padx=10, pady=5, sticky="ew")
        
        # GIF
        self.gif_details_frame = ctk.CTkFrame(self.anim_details_frame, fg_color="transparent")
        self.gif_details_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(self.gif_details_frame, text="Colori GIF:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.gif_colors_slider = ctk.CTkSlider(self.gif_details_frame, from_=2, to=256, number_of_steps=255, variable=self.gif_colors_var, command=self.gif_colors_slider_callback, button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], progress_color=COLOR_PALETTE["accent_green"])
        self.gif_colors_slider.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.gif_colors_label = ctk.CTkLabel(self.gif_details_frame, text=str(int(self.gif_colors_var.get())), font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_PALETTE["accent_green"])
        self.gif_colors_label.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkLabel(self.gif_details_frame, text="Dithering GIF:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        self.gif_dither_menu = ctk.CTkOptionMenu(self.gif_details_frame, values=["bayer:bayer_scale=3", "bayer:bayer_scale=1", "bayer:bayer_scale=5", "floyd_steinberg", "none"], variable=self.gif_dither_var, command=lambda _: self.update_command_preview(), fg_color=COLOR_PALETTE["accent_green"], button_color=COLOR_PALETTE["accent_green"], button_hover_color=COLOR_PALETTE["accent_green_hover"], text_color=COLOR_PALETTE["text_dark"])
        self.gif_dither_menu.grid(row=1, column=2, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.gif_details_frame, text="Ottimizzazione:", anchor="w", text_color=COLOR_PALETTE["text"]).grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        self.gif_optimize_switch = ctk.CTkSwitch(self.gif_details_frame, text="Gifsicle", variable=self.gif_optimize_var, command=self.on_gif_optimize_change, progress_color=COLOR_PALETTE["accent_green"])
        self.gif_optimize_switch.grid(row=1, column=3, padx=10, pady=5, sticky="ew")

        # Inizializza UI video
        self.update_video_ui_from_preset()
        
        # Mostra log di avvio dopo che l'interfaccia è pronta
        self.after(500, lambda: self.log_startup_messages(load_error))

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
            # Configurazione cross-platform per subprocess
            kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'universal_newlines': True,
                'encoding': 'utf-8'
            }
            
            # startupinfo è specifico per Windows
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                kwargs['startupinfo'] = startupinfo
            
            self.ffmpeg_process = subprocess.Popen(command, **kwargs)

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

    def log_startup_messages(self, load_error):
        if load_error:
            self.log(f"AVVISO CARICAMENTO PRESET: {load_error}\n")
        else:
            self.log("INFO: presets.json caricato correttamente.\n")
            
        # Controlla la presenza di gifsicle all'avvio
        if not shutil.which("gifsicle"):
            self.log("INFO: Gifsicle non trovato nel sistema. L'ottimizzazione delle GIF sarà disabilitata.\n")

    def process_queue(self, file_queue, is_manual):
        """Gestisce la coda di elaborazione dei file, sia in modalità manuale che automatica."""
        command_template = self.command_preview.get("1.0", tk.END).strip() if is_manual else None
        
        if is_manual and ("%%INPUT%%" not in command_template or "%%OUTPUT%%" not in command_template):
            self.log("ERRORE: Il template in modalità manuale deve contenere i segnaposto %%INPUT%% e %%OUTPUT%%.\n")
            self.toggle_ui_state(running=False)
            return

        total_files = len(file_queue)
        mode = self.mode_var.get()

        # Validazione anticipata degli input di animazione
        if mode == "Animazioni":
            valid, err_msg = self.validate_anim_inputs()
            if not valid:
                self.log(f"ERRORE DI VALIDAZIONE: {err_msg}\n")
                self.toggle_ui_state(running=False)
                return

        for i, input_filepath_str in enumerate(file_queue):
            if not self.is_running:
                break
            
            current_file_index = i + 1
            input_filepath = Path(input_filepath_str)
            
            if mode == "Video":
                output_filepath = self.generate_output_path(input_filepath)
                output_filepath.parent.mkdir(parents=True, exist_ok=True)
                
                command = []
                if is_manual:
                    concrete_command_str = command_template.replace("%%INPUT%%", f'"{input_filepath}"').replace("%%OUTPUT%%", f'"{output_filepath}"')
                    ffmpeg_path = self.find_ffmpeg()
                    if not ffmpeg_path:
                        self.log(f"ERRORE: ffmpeg non trovato per il file {input_filepath.name}.\n")
                        continue
                    command_args = shlex.split(concrete_command_str)
                    command_args[0] = ffmpeg_path
                    command = command_args
                else:
                    command = self.build_command(str(input_filepath))
                    
                if not command:
                    self.log(f"ERRORE: Impossibile generare il comando per {input_filepath.name}.\n")
                    continue
                    
                self.run_ffmpeg_with_progress(command, current_file_index, total_files, input_filepath.name)
                
            else:
                # Categoria Animazioni
                format_ext = self.anim_format_var.get()
                output_filepath = self.generate_output_path(input_filepath)
                output_filepath.parent.mkdir(parents=True, exist_ok=True)
                
                ffmpeg_path = self.find_ffmpeg()
                if not ffmpeg_path:
                    self.log("ERRORE: ffmpeg non trovato. Elaborazione interrotta.\n")
                    break
                    
                fps = int(self.anim_fps_var.get())
                width_str = self.anim_width_var.get()
                width = int(self.anim_custom_width_var.get()) if width_str == "Custom" else int(width_str)
                
                if is_manual:
                    concrete_command_str = command_template.replace("%%INPUT%%", f'"{input_filepath}"').replace("%%OUTPUT%%", f'"{output_filepath}"')
                    command_args = shlex.split(concrete_command_str)
                    command_args[0] = ffmpeg_path
                    self.run_ffmpeg_with_progress(command_args, current_file_index, total_files, input_filepath.name)
                else:
                    if format_ext == "WebP":
                        q = int(self.webp_quality_var.get())
                        method = int(self.webp_method_var.get())
                        command = command_builder.build_webp_command(
                            ffmpeg_path, str(input_filepath), str(output_filepath), fps, width, q, method
                        )
                        self.run_ffmpeg_with_progress(command, current_file_index, total_files, input_filepath.name)
                        
                    elif format_ext == "AVIF":
                        crf = int(self.avif_crf_var.get())
                        preset = int(self.avif_preset_var.get())
                        enc = self.avif_encoder_var.get()
                        
                        if enc == "libsvtav1":
                            command = command_builder.build_avif_svt_command(
                                ffmpeg_path, str(input_filepath), str(output_filepath), fps, width, crf, preset
                            )
                        else:
                            command = command_builder.build_avif_aom_command(
                                ffmpeg_path, str(input_filepath), str(output_filepath), fps, width, crf
                            )
                        self.run_ffmpeg_with_progress(command, current_file_index, total_files, input_filepath.name)
                        
                    elif format_ext == "GIF":
                        colors = int(self.gif_colors_var.get())
                        dither = self.gif_dither_var.get()
                        
                        palette_path = output_filepath.parent / f"{output_filepath.stem}_palette.png"
                        try:
                            # 1. Palette
                            self.progress_label.configure(text=f"Processando File {current_file_index}/{total_files} (Palette): {input_filepath.name}")
                            self.progress_bar.set(0)
                            palette_cmd = command_builder.build_gif_palette_command(
                                ffmpeg_path, str(input_filepath), str(palette_path), fps, width, colors
                            )
                            self.log(f"\n--- [1/2] Generazione tavolozza colori per GIF: {input_filepath.name} ---\n")
                            
                            startupinfo = None
                            if platform.system() == 'Windows':
                                startupinfo = subprocess.STARTUPINFO()
                                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            
                            res = subprocess.run(palette_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo, encoding='utf-8')
                            self.log(res.stdout)
                            
                            if res.returncode != 0:
                                self.log(f"\n--- ERRORE: Generazione palette fallita per {input_filepath.name}. Controlla il log. ---\n")
                                continue
                                
                            if not self.is_running:
                                break
                                
                            # 2. Render GIF
                            render_cmd = command_builder.build_gif_render_command(
                                ffmpeg_path, str(input_filepath), str(palette_path), str(output_filepath), fps, width, dither
                            )
                            self.log(f"\n--- [2/2] Creazione file GIF: {input_filepath.name} ---\n")
                            self.run_ffmpeg_with_progress(render_cmd, current_file_index, total_files, input_filepath.name)
                            
                            # 3. Gifsicle
                            if self.is_running and self.gif_optimize_var.get():
                                gifsicle_path = shutil.which("gifsicle")
                                if gifsicle_path:
                                    self.progress_label.configure(text=f"Processando File {current_file_index}/{total_files} (Ottimizzazione GIF): {input_filepath.name}")
                                    self.progress_bar.set(1.0)
                                    temp_opt_path = output_filepath.parent / f"{output_filepath.name}.opt.tmp"
                                    opt_cmd = command_builder.build_gifsicle_command(
                                        gifsicle_path, str(output_filepath), str(temp_opt_path), colors, 100
                                    )
                                    self.log(f"\n--- [Opzionale] Ottimizzazione GIF con Gifsicle: {input_filepath.name} ---\n")
                                    
                                    opt_res = subprocess.run(opt_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo, encoding='utf-8')
                                    self.log(opt_res.stdout)
                                    
                                    if opt_res.returncode == 0 and temp_opt_path.exists():
                                        try:
                                            output_filepath.unlink(missing_ok=True)
                                            temp_opt_path.rename(output_filepath)
                                            self.log("Ottimizzazione completata con successo.\n")
                                        except Exception as e:
                                            self.log(f"ERRORE durante la sostituzione del file ottimizzato: {e}\n")
                                    else:
                                        self.log(f"ERRORE: Gifsicle fallito con codice {opt_res.returncode}.\n")
                                        if temp_opt_path.exists():
                                            temp_opt_path.unlink()
                                            
                        finally:
                            if palette_path.exists():
                                try:
                                    palette_path.unlink()
                                except Exception as e:
                                    self.log(f"Impossibile rimuovere il file temporaneo {palette_path}: {e}\n")

        if self.is_running:
            self.log(f"\n--- Elaborazione della coda conclusa. ---\n")
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
        """Genera il percorso del file di output in base alla modalità corrente."""
        mode = self.mode_var.get()
        if mode == "Video":
            return command_builder.generate_video_output_path(
                str(input_path), self.current_preset_config, int(self.cq_slider.get()), self.preset_var.get()
            )
        else:
            return command_builder.generate_animation_output_path(
                str(input_path), self.anim_format_var.get()
            )

    def update_command_preview(self, force_template=False):
        # Guardia: durante __init__ i widget potrebbero non esistere ancora
        if not hasattr(self, 'manual_edit_switch') or not hasattr(self, 'command_preview'):
            return
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
        mode = self.mode_var.get()
        ffmpeg_path = self.find_ffmpeg() or "ffmpeg"
        
        preview_str = ""
        
        if mode == "Video":
            preset_cfg = self.current_preset_config
            cq = int(self.cq_slider.get())
            preset = self.preset_var.get()
            scale = self.scale_var.get()
            
            out_path = str(command_builder.generate_video_output_path(first_file, preset_cfg, cq, preset))
            command_list = command_builder.build_video_command(
                ffmpeg_path, first_file, out_path, preset_cfg, cq, preset, scale
            )
            
            if force_template:
                try:
                    input_index = command_list.index(str(Path(first_file)))
                    output_index = command_list.index(out_path)
                    command_list[input_index] = "%%INPUT%%"
                    command_list[output_index] = "%%OUTPUT%%"
                except ValueError:
                    pass
            
            if platform.system() == 'Windows':
                preview_str = subprocess.list2cmdline(command_list)
            else:
                preview_str = shlex.join(command_list)
                
        else:
            fmt = self.anim_format_var.get()
            fps = int(self.anim_fps_var.get())
            
            width_str = self.anim_width_var.get()
            if width_str == "Custom":
                try:
                    width = int(self.anim_custom_width_var.get())
                except ValueError:
                    width = 1920
            else:
                width = int(width_str)
                
            out_path = str(command_builder.generate_animation_output_path(first_file, fmt))
            
            input_placeholder = "%%INPUT%%" if force_template else first_file
            output_placeholder = "%%OUTPUT%%" if force_template else out_path
            
            if fmt == "WebP":
                q = int(self.webp_quality_var.get())
                method = int(self.webp_method_var.get())
                cmd_list = command_builder.build_webp_command(
                    ffmpeg_path, input_placeholder, output_placeholder, fps, width, q, method
                )
                if platform.system() == 'Windows':
                    preview_str = subprocess.list2cmdline(cmd_list)
                else:
                    preview_str = shlex.join(cmd_list)
                    
            elif fmt == "AVIF":
                crf = int(self.avif_crf_var.get())
                preset = int(self.avif_preset_var.get())
                enc = self.avif_encoder_var.get()
                if enc == "libsvtav1":
                    cmd_list = command_builder.build_avif_svt_command(
                        ffmpeg_path, input_placeholder, output_placeholder, fps, width, crf, preset
                    )
                else:
                    cmd_list = command_builder.build_avif_aom_command(
                        ffmpeg_path, input_placeholder, output_placeholder, fps, width, crf
                    )
                if platform.system() == 'Windows':
                    preview_str = subprocess.list2cmdline(cmd_list)
                else:
                    preview_str = shlex.join(cmd_list)
                    
            elif fmt == "GIF":
                colors = int(self.gif_colors_var.get())
                dither = self.gif_dither_var.get()
                
                palette_placeholder = "%%PALETTE_TMP%%" if force_template else str(Path(out_path).parent / f"{Path(out_path).stem}_palette.png")
                
                palette_cmd = command_builder.build_gif_palette_command(
                    ffmpeg_path, input_placeholder, palette_placeholder, fps, width, colors
                )
                render_cmd = command_builder.build_gif_render_command(
                    ffmpeg_path, input_placeholder, palette_placeholder, output_placeholder, fps, width, dither
                )
                
                gifsicle_path = shutil.which("gifsicle") or "gifsicle"
                opt_cmd = command_builder.build_gifsicle_command(
                    gifsicle_path, output_placeholder, output_placeholder, colors, 100
                )
                
                if platform.system() == 'Windows':
                    p1 = subprocess.list2cmdline(palette_cmd)
                    p2 = subprocess.list2cmdline(render_cmd)
                    p3 = subprocess.list2cmdline(opt_cmd)
                else:
                    p1 = shlex.join(palette_cmd)
                    p2 = shlex.join(render_cmd)
                    p3 = shlex.join(opt_cmd)
                    
                preview_str = (
                    f"# [1/3] Generazione tavolozza\n{p1}\n\n"
                    f"# [2/3] Creazione GIF\n{p2}\n\n"
                    f"# [3/3] Ottimizzazione GIF (opzionale, se gifsicle è presente)\n{p3}"
                )

        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert("1.0", preview_str)
        
        if not self.manual_edit_switch.get() == 1:
            self.command_preview.configure(state="disabled")

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
            self.mode_selector.configure(state="disabled")
            self.set_options_state("disabled")
            self.start_button.configure(text="Avvia Coda Manuale")
            self.log("INFO: Modalità manuale attivata. Il comando verrà usato come template per tutti i file.\n"
                     "      Assicurati che i segnaposto %%INPUT%% e %%OUTPUT%% siano presenti.\n")
            self.update_command_preview(force_template=True)
        else:
            self.command_preview.configure(state="disabled")
            self.mode_selector.configure(state="normal")
            self.on_mode_change(self.mode_var.get())
            self.update_command_preview()

    def add_files_to_list(self, files):
        current_files_text = self.file_list_box.get("1.0", tk.END)
        for f in files:
            normalized_f = str(Path(f).resolve())
            if normalized_f not in current_files_text:
                self.file_list_box.insert(tk.END, normalized_f + "\n")
        self.update_command_preview()

    def clear_file_list(self):
        self.file_list_box.delete("1.0", tk.END)
        self.update_command_preview()
        
    def handle_drop(self, event):
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
        
        self.mode_selector.configure(state=state)
        self.set_options_state(state)
        
        if not running:
            is_manual_mode = self.manual_edit_switch.get() == 1
            if is_manual_mode:
                self.toggle_manual_edit_mode()
            else:
                self.on_mode_change(self.mode_var.get())
            
            self.progress_label.configure(text="Pronto.")
            self.progress_bar.set(0)

    def set_options_state(self, state):
        self.codec_menu.configure(state=state)
        self.preset_menu.configure(state=state)
        self.cq_slider.configure(state=state)
        self.scale_menu.configure(state=state)
        
        self.anim_format_menu.configure(state=state)
        self.anim_fps_slider.configure(state=state)
        self.anim_width_menu.configure(state=state)
        self.custom_width_entry.configure(state=state)
        
        self.webp_q_slider.configure(state=state)
        self.webp_method_menu.configure(state=state)
        self.avif_crf_slider.configure(state=state)
        self.avif_preset_menu.configure(state=state)
        self.avif_enc_menu.configure(state=state)
        self.gif_colors_slider.configure(state=state)
        self.gif_dither_menu.configure(state=state)
        self.gif_optimize_switch.configure(state=state)

    def build_command(self, input_file):
        """Genera il comando FFmpeg per i preset video (retrocompatibilità)."""
        ffmpeg_path = self.find_ffmpeg()
        if not ffmpeg_path: 
            self.log("ERRORE: ffmpeg non trovato. Assicurati sia nel PATH o nella cartella dell'app.\n")
            return None

        preset_cfg = self.current_preset_config
        cq = int(self.cq_slider.get())
        preset = self.preset_var.get()
        scale = self.scale_var.get()
        output_file = str(command_builder.generate_video_output_path(input_file, preset_cfg, cq, preset))
        
        return command_builder.build_video_command(
            ffmpeg_path, input_file, output_file, preset_cfg, cq, preset, scale
        )

    def update_cq_label(self, value):
        self.cq_label.configure(text=f"{int(value)}")
        self.update_command_preview()

    def update_ui_for_codec(self, codec=None):
        if codec:
            self.codec_var.set(codec)
        self.update_video_ui_from_preset()

    def on_mode_change(self, mode):
        if mode == "Video":
            self.anim_options_frame.grid_forget()
            self.video_options_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
            self.start_button.configure(text="Avvia Compressione")
            self.update_video_ui_from_preset()
        else:
            self.video_options_frame.grid_forget()
            self.anim_options_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
            self.start_button.configure(text="Avvia Animazione")
            self.update_anim_ui_from_format()

    def update_video_ui_from_preset(self):
        preset_name = self.codec_var.get()
        preset_cfg = next((p for p in self.presets_data.get("video_presets", []) if p["name"] == preset_name), None)
        if not preset_cfg:
            return
        
        self.current_preset_config = preset_cfg
        ui_cfg = preset_cfg.get("ui", {})
        
        # 1. Preset Menu
        p_cfg = ui_cfg.get("preset", {})
        if p_cfg.get("enabled", False):
            self.preset_menu.configure(state="normal")
            options = p_cfg.get("options", ["p1", "p2", "p3", "p4", "p5", "p6", "p7"])
            self.preset_menu.configure(values=options)
            curr_val = self.preset_var.get()
            if curr_val not in options:
                self.preset_var.set(p_cfg.get("default", "p6"))
        else:
            self.preset_menu.configure(state="disabled")
            
        # 2. Slider Qualità (CQ o Quality)
        cq_cfg = ui_cfg.get("cq", {})
        quality_cfg = ui_cfg.get("quality", {})
        slider_cfg = cq_cfg if cq_cfg.get("enabled", False) else (quality_cfg if quality_cfg.get("enabled", False) else None)
        
        if slider_cfg:
            self.cq_slider.configure(state="normal")
            self.cq_slider.configure(from_=slider_cfg.get("min", 0), to=slider_cfg.get("max", 51), number_of_steps=slider_cfg.get("max", 51) - slider_cfg.get("min", 0) + 1)
            self.cq_title_label.configure(text=slider_cfg.get("label", "CQ (Qualità):"))
            self.cq_slider.set(slider_cfg.get("default", 23))
            self.cq_label.configure(text=str(int(self.cq_slider.get())))
        else:
            self.cq_slider.configure(state="disabled")
            self.cq_title_label.configure(text="Qualità (Disabilitata):")
            self.cq_label.configure(text="-")
            
        # 3. Scaling Menu
        scale_cfg = ui_cfg.get("scale", {})
        if scale_cfg.get("enabled", False):
            self.scale_menu.configure(state="normal")
        else:
            self.scale_menu.configure(state="disabled")
            self.scale_var.set("Nessuno")
            
        self.update_command_preview()

    def update_anim_ui_from_format(self):
        fmt = self.anim_format_var.get()
        
        self.webp_details_frame.grid_forget()
        self.avif_details_frame.grid_forget()
        self.gif_details_frame.grid_forget()
        
        if fmt == "WebP":
            self.webp_details_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
        elif fmt == "AVIF":
            self.avif_details_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
            self.check_avif_encoder_warning()
        elif fmt == "GIF":
            self.gif_details_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
            self.check_gifsicle_warning()
            
        self.update_custom_width_visibility()

    def update_fps_label(self, value):
        self.fps_title_label.configure(text=f"FPS ({int(value)}):")
        self.update_command_preview()

    def webp_q_slider_callback(self, value):
        self.webp_q_label.configure(text=str(int(value)))
        self.update_command_preview()

    def avif_crf_slider_callback(self, value):
        self.avif_crf_label.configure(text=str(int(value)))
        self.update_command_preview()

    def gif_colors_slider_callback(self, value):
        self.gif_colors_label.configure(text=str(int(value)))
        self.update_command_preview()

    def update_custom_width_visibility(self):
        if self.anim_width_var.get() == "Custom":
            self.custom_width_title_label.grid(row=0, column=3, padx=15, pady=(10,0), sticky="ew")
            self.custom_width_entry.grid(row=1, column=3, padx=15, pady=(5,10), sticky="ew")
        else:
            self.custom_width_title_label.grid_forget()
            self.custom_width_entry.grid_forget()
        self.update_command_preview()

    def on_avif_encoder_change(self, enc):
        self.check_avif_encoder_warning()
        self.update_command_preview()

    def on_gif_optimize_change(self):
        self.check_gifsicle_warning()
        self.update_command_preview()

    def check_avif_encoder_warning(self):
        if self.anim_format_var.get() == "AVIF":
            enc = self.avif_encoder_var.get()
            ffmpeg_path = self.find_ffmpeg()
            if ffmpeg_path:
                if not hasattr(self, '_available_encoders'):
                    self._available_encoders = self.query_ffmpeg_encoders(ffmpeg_path)
                
                if enc not in self._available_encoders:
                    self.log(f"ATTENZIONE: L'encoder AVIF '{enc}' non sembra essere supportato da questa build di FFmpeg!\n"
                             f"            La conversione in AVIF potrebbe fallire.\n")

    def check_gifsicle_warning(self):
        if self.anim_format_var.get() == "GIF" and self.gif_optimize_var.get():
            if not shutil.which("gifsicle"):
                self.log("AVVISO: Gifsicle non trovato nel sistema. L'ottimizzazione delle GIF sarà saltata.\n"
                         "        Puoi installare Gifsicle e aggiungerlo al PATH per abilitare l'ottimizzazione.\n")

    def query_ffmpeg_encoders(self, ffmpeg_path) -> set[str]:
        try:
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            res = subprocess.run([ffmpeg_path, "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, timeout=5)
            encoders = set()
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0].startswith('V'):
                    encoders.add(parts[1])
            return encoders
        except Exception:
            return {"libsvtav1", "libaom-av1"}

    def validate_anim_inputs(self) -> tuple[bool, str]:
        try:
            fps = int(self.anim_fps_var.get())
            if fps <= 0:
                return False, "Gli FPS devono essere maggiori di 0."
        except ValueError:
            return False, "Gli FPS devono essere un numero intero valido."
            
        width_mode = self.anim_width_var.get()
        if width_mode == "Custom":
            try:
                width = int(self.anim_custom_width_var.get())
                if width <= 0:
                    return False, "La larghezza custom deve essere maggiore di 0."
            except ValueError:
                return False, "La larghezza custom deve essere un numero intero valido."
                
        if self.anim_format_var.get() == "WebP":
            try:
                q = int(self.webp_quality_var.get())
                if not (0 <= q <= 100):
                    return False, "La qualità WebP deve essere compresa tra 0 e 100."
            except ValueError:
                return False, "La qualità WebP deve essere un numero valido."
                
        elif self.anim_format_var.get() == "AVIF":
            try:
                crf = int(self.avif_crf_var.get())
                if not (0 <= crf <= 63):
                    return False, "Il CRF AVIF deve essere compreso tra 0 e 63."
            except ValueError:
                return False, "Il CRF AVIF deve essere un numero valido."
                
        elif self.anim_format_var.get() == "GIF":
            try:
                colors = int(self.gif_colors_var.get())
                if not (2 <= colors <= 256):
                    return False, "I colori GIF devono essere compresi tra 2 e 256."
            except ValueError:
                return False, "I colori GIF devono essere un numero valido."
                
        return True, ""

    def find_ffmpeg(self):
        """Trova ffmpeg in modo cross-platform"""
        # Prima cerca nel PATH di sistema
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        
        # Poi cerca nella cartella locale
        try:
            # Percorso per l'eseguibile PyInstaller
            base_path = sys._MEIPASS
        except AttributeError:
            # Percorso per l'esecuzione normale come script .py
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Cross-platform: cerca sia ffmpeg.exe (Windows) che ffmpeg (Linux/Mac)
        if platform.system() == 'Windows':
            local_path = os.path.join(base_path, 'ffmpeg.exe')
        else:
            local_path = os.path.join(base_path, 'ffmpeg')
            
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

    # Prova a impostare l'icona sulla finestra (solo Windows)
    def set_window_icon():
        if platform.system() == 'Windows':
            try:
                app_window.wm_iconbitmap('icona.ico')
            except tk.TclError:
                print("Icona 'icona.ico' non trovata.")

    # Imposta l'icona dopo che la finestra è stata completamente creata
    app_window.after(100, set_window_icon)

    # Gestisci la chiusura
    def on_closing():
        app_window.on_closing()
        hidden_root.destroy()

    app_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Avvia il loop principale
    hidden_root.mainloop()
