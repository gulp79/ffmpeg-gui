from pathlib import Path

def generate_video_output_path(input_path_str: str, preset_config: dict, cq_value: int, preset_value: str) -> Path:
    """
    Genera il percorso del file di output per i preset video.
    Gestisce la creazione di proxy e l'applicazione di estensioni/suffissi personalizzati dal JSON.
    """
    input_path = Path(input_path_str)
    preset_id = preset_config.get("id", "")
    
    # Se è un proxy, posiziona in parent/proxy/name
    if preset_id.startswith("proxy"):
        proxy_dir = input_path.parent / "proxy"
        return proxy_dir / input_path.name
    
    # Costruisci il suffisso
    suffix_template = preset_config.get("output_suffix", "")
    suffix = suffix_template.replace("{cq}", str(cq_value)).replace("{quality}", str(cq_value)).replace("{preset}", str(preset_value))
    
    # Estensione
    ext = preset_config.get("output_extension")
    if not ext:
        ext = input_path.suffix
        
    new_name = f"{input_path.stem}{suffix}{ext}"
    return input_path.parent / new_name

def generate_animation_output_path(input_path_str: str, format_ext: str) -> Path:
    """
    Genera il percorso del file di output per le animazioni (WebP, AVIF, GIF).
    Usa il suffisso '_anim'.
    """
    input_path = Path(input_path_str)
    ext = format_ext.lower().strip()
    if not ext.startswith("."):
        ext = f".{ext}"
    new_name = f"{input_path.stem}_anim{ext}"
    return input_path.parent / new_name

def build_video_command(ffmpeg_path: str, input_file: str, output_file: str, preset_config: dict, cq_value: int, preset_value: str, scale_value: str) -> list[str]:
    """
    Costruisce la lista di argomenti per il comando FFmpeg per l'encoding video basato su preset.
    """
    cmd = [ffmpeg_path, "-y"]
    
    ffmpeg_cfg = preset_config.get("ffmpeg", {})
    
    # 1. Hardware Acceleration (se presente)
    hwaccel = ffmpeg_cfg.get("hwaccel", [])
    cmd.extend(hwaccel)
    
    # 2. Input
    cmd.extend(["-i", input_file])
    
    # 3. Codec Video
    video_codec = ffmpeg_cfg.get("video_codec", [])
    cmd.extend(video_codec)
    
    # 4. Preset (sostituzione template)
    preset_template = ffmpeg_cfg.get("preset_template", [])
    for arg in preset_template:
        cmd.append(arg.replace("{preset}", str(preset_value)))
        
    # 5. Rate Control (se presente)
    rate_control = ffmpeg_cfg.get("rate_control", [])
    cmd.extend(rate_control)
    
    # 6. Quality / CQ (sostituzione template)
    quality_template = ffmpeg_cfg.get("quality_template", [])
    for arg in quality_template:
        replaced = arg.replace("{cq}", str(cq_value)).replace("{quality}", str(cq_value))
        cmd.append(replaced)
        
    # 7. Scaling (se abilitato per il preset e non nullo)
    ui_cfg = preset_config.get("ui", {})
    if ui_cfg.get("scale", {}).get("enabled", False) and scale_value != "Nessuno":
        scale_map = {"4k": "2160", "2k": "1440", "1080p": "1080", "720p": "720", "576p": "576", "480p": "480"}
        scale_height = scale_map.get(scale_value)
        if scale_height:
            # Se usiamo accelerazione CUDA, usa scale_cuda, altrimenti scale standard
            is_cuda = any("cuda" in str(arg).lower() for arg in hwaccel)
            if is_cuda:
                cmd.extend(["-vf", f"scale_cuda=-2:{scale_height}"])
            else:
                cmd.extend(["-vf", f"scale=-2:{scale_height}"])
                
    # 8. Parametri video extra (con eventuale rimpiazzo qualità)
    extra_video_args = ffmpeg_cfg.get("extra_video_args", [])
    for arg in extra_video_args:
        replaced = arg.replace("{cq}", str(cq_value)).replace("{quality}", str(cq_value))
        cmd.append(replaced)
        
    # 9. Parametri container (es. faststart)
    container_args = ffmpeg_cfg.get("container_args", [])
    cmd.extend(container_args)
    
    # 10. Parametri audio (es. copy o mp3)
    audio_args = ffmpeg_cfg.get("audio_args", [])
    cmd.extend(audio_args)
    
    # 11. Output File
    cmd.append(output_file)
    
    return cmd

def build_webp_command(ffmpeg_path: str, input_file: str, output_file: str, fps: int, width: int, quality: int, method: int) -> list[str]:
    """Costruisce la lista di argomenti per l'animazione WebP."""
    return [
        ffmpeg_path, "-y", "-hide_banner",
        "-i", input_file,
        "-vf", f"fps={fps},scale={width}:-2:flags=lanczos",
        "-c:v", "libwebp",
        "-loop", "0",
        "-q:v", str(quality),
        "-compression_level", str(method),
        output_file
    ]

def build_avif_svt_command(ffmpeg_path: str, input_file: str, output_file: str, fps: int, width: int, crf: int, preset: int) -> list[str]:
    """Costruisce la lista di argomenti per l'animazione AVIF con encoder libsvtav1."""
    return [
        ffmpeg_path, "-y", "-hide_banner",
        "-i", input_file,
        "-vf", f"fps={fps},scale={width}:-2:flags=lanczos",
        "-c:v", "libsvtav1",
        "-crf", str(crf),
        "-preset", str(preset),
        "-pix_fmt", "yuv420p",
        output_file
    ]

def build_avif_aom_command(ffmpeg_path: str, input_file: str, output_file: str, fps: int, width: int, crf: int) -> list[str]:
    """Costruisce la lista di argomenti per l'animazione AVIF con encoder libaom-av1."""
    return [
        ffmpeg_path, "-y", "-hide_banner",
        "-i", input_file,
        "-vf", f"fps={fps},scale={width}:-2:flags=lanczos",
        "-c:v", "libaom-av1",
        "-crf", str(crf),
        "-b:v", "0",
        "-cpu-used", "4",
        "-pix_fmt", "yuv420p",
        output_file
    ]

def build_gif_palette_command(ffmpeg_path: str, input_file: str, palette_path: str, fps: int, width: int, colors: int) -> list[str]:
    """Costruisce la lista di argomenti per generare la palette temporanea della GIF."""
    return [
        ffmpeg_path, "-y", "-hide_banner",
        "-i", input_file,
        "-vf", f"fps={fps},scale={width}:-2:flags=lanczos,palettegen=max_colors={colors}",
        palette_path
    ]

def build_gif_render_command(ffmpeg_path: str, input_file: str, palette_path: str, output_file: str, fps: int, width: int, dither: str) -> list[str]:
    """Costruisce la lista di argomenti per generare il file GIF combinando input e palette."""
    return [
        ffmpeg_path, "-y", "-hide_banner",
        "-i", input_file,
        "-i", palette_path,
        "-filter_complex", f"fps={fps},scale={width}:-2:flags=lanczos[x];[x][1:v]paletteuse=dither={dither}",
        output_file
    ]

def build_gifsicle_command(gifsicle_path: str, input_file: str, output_file: str, colors: int, lossy: int) -> list[str]:
    """Costruisce la lista di argomenti per l'ottimizzazione della GIF con Gifsicle."""
    return [
        gifsicle_path, "-O3",
        f"--lossy={lossy}",
        "--colors", str(colors),
        input_file,
        "-o", output_file
    ]
