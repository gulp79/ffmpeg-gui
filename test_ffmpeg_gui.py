import json
import pytest
from pathlib import Path
import presets_manager
import command_builder

def test_get_default_presets():
    presets = presets_manager.get_default_presets()
    assert presets["schema_version"] == 1
    assert "video_presets" in presets
    assert "animation_presets" in presets
    
    # Valida che sia strutturato correttamente
    valido, err = presets_manager.validate_presets_json(presets)
    assert valido is True
    assert err == ""

def test_validate_presets_invalid():
    # Struttura non dizionario
    valido, err = presets_manager.validate_presets_json([])
    assert valido is False
    assert "oggetto JSON" in err
    
    # Campo schema_version mancante
    valido, err = presets_manager.validate_presets_json({"video_presets": []})
    assert valido is False
    assert "schema_version" in err

    # Preset video con campo mancante
    invalido_preset = {
        "schema_version": 1,
        "video_presets": [
            {
                "id": "av1",
                "name": "AV1 Test"
                # manca ffmpeg e ui
            }
        ],
        "animation_presets": {"defaults": {}}
    }
    valido, err = presets_manager.validate_presets_json(invalido_preset)
    assert valido is False
    assert "manca il campo obbligatorio" in err

def test_generate_video_output_path():
    preset_cfg = {
        "id": "h265_test",
        "output_suffix": "_h265_cq{cq}_{preset}",
        "output_extension": ".mkv"
    }
    input_file = "C:/Videos/my_video.mp4"
    output = command_builder.generate_video_output_path(input_file, preset_cfg, cq_value=23, preset_value="p5")
    
    assert output.name == "my_video_h265_cq23_p5.mkv"
    assert output.parent == Path("C:/Videos")

def test_generate_proxy_output_path():
    preset_cfg = {
        "id": "proxy_h264",
        "output_suffix": "",
        "output_extension": None
    }
    input_file = "C:/Videos/my_video.mp4"
    output = command_builder.generate_video_output_path(input_file, preset_cfg, cq_value=0, preset_value="p1")
    
    # Proxy deve finire in parent/proxy/name
    assert output.name == "my_video.mp4"
    assert output.parent == Path("C:/Videos/proxy")

def test_build_video_command():
    preset_cfg = {
        "id": "av1_nvenc",
        "ffmpeg": {
            "hwaccel": ["-hwaccel", "cuda"],
            "video_codec": ["-c:v", "av1_nvenc"],
            "rate_control": ["-rc", "vbr"],
            "quality_template": ["-cq", "{cq}"],
            "preset_template": ["-preset", "{preset}"],
            "extra_video_args": ["-b:v", "0", "-g", "120"],
            "container_args": ["-movflags", "+faststart"],
            "audio_args": ["-c:a", "copy"]
        },
        "ui": {
            "scale": {
                "enabled": True
            }
        }
    }
    
    # Test senza scaling
    cmd = command_builder.build_video_command(
        ffmpeg_path="ffmpeg",
        input_file="input.mp4",
        output_file="output.mp4",
        preset_config=preset_cfg,
        cq_value=25,
        preset_value="p4",
        scale_value="Nessuno"
    )
    
    expected = [
        "ffmpeg", "-y", "-hwaccel", "cuda",
        "-i", "input.mp4",
        "-c:v", "av1_nvenc",
        "-preset", "p4",
        "-rc", "vbr",
        "-cq", "25",
        "-b:v", "0", "-g", "120",
        "-movflags", "+faststart",
        "-c:a", "copy",
        "output.mp4"
    ]
    assert cmd == expected

    # Test con scaling (CUDA)
    cmd_scaled = command_builder.build_video_command(
        ffmpeg_path="ffmpeg",
        input_file="input.mp4",
        output_file="output.mp4",
        preset_config=preset_cfg,
        cq_value=25,
        preset_value="p4",
        scale_value="1080p"
    )
    assert "-vf" in cmd_scaled
    assert "scale_cuda=-2:1080" in cmd_scaled

    # Test con scaling (CPU - no cuda in hwaccel)
    preset_cfg_cpu = dict(preset_cfg)
    preset_cfg_cpu["ffmpeg"] = dict(preset_cfg["ffmpeg"])
    preset_cfg_cpu["ffmpeg"]["hwaccel"] = []
    cmd_scaled_cpu = command_builder.build_video_command(
        ffmpeg_path="ffmpeg",
        input_file="input.mp4",
        output_file="output.mp4",
        preset_config=preset_cfg_cpu,
        cq_value=25,
        preset_value="p4",
        scale_value="1080p"
    )
    assert "-vf" in cmd_scaled_cpu
    assert "scale=-2:1080" in cmd_scaled_cpu

def test_build_webp_command():
    cmd = command_builder.build_webp_command(
        ffmpeg_path="ffmpeg",
        input_file="in.mp4",
        output_file="out.webp",
        fps=10,
        width=1280,
        quality=75,
        method=5
    )
    assert cmd == [
        "ffmpeg", "-y", "-hide_banner",
        "-i", "in.mp4",
        "-vf", "fps=10,scale=1280:-2:flags=lanczos",
        "-c:v", "libwebp",
        "-loop", "0",
        "-q:v", "75",
        "-compression_level", "5",
        "out.webp"
    ]

def test_build_avif_commands():
    # SVT
    cmd_svt = command_builder.build_avif_svt_command(
        ffmpeg_path="ffmpeg",
        input_file="in.mp4",
        output_file="out.avif",
        fps=8,
        width=720,
        crf=30,
        preset=4
    )
    assert cmd_svt == [
        "ffmpeg", "-y", "-hide_banner",
        "-i", "in.mp4",
        "-vf", "fps=8,scale=720:-2:flags=lanczos",
        "-c:v", "libsvtav1",
        "-crf", "30",
        "-preset", "4",
        "-pix_fmt", "yuv420p",
        "out.avif"
    ]
    
    # AOM
    cmd_aom = command_builder.build_avif_aom_command(
        ffmpeg_path="ffmpeg",
        input_file="in.mp4",
        output_file="out.avif",
        fps=8,
        width=720,
        crf=30
    )
    assert cmd_aom == [
        "ffmpeg", "-y", "-hide_banner",
        "-i", "in.mp4",
        "-vf", "fps=8,scale=720:-2:flags=lanczos",
        "-c:v", "libaom-av1",
        "-crf", "30",
        "-b:v", "0",
        "-cpu-used", "4",
        "-pix_fmt", "yuv420p",
        "out.avif"
    ]

def test_build_gif_pipeline():
    cmd_palette = command_builder.build_gif_palette_command(
        ffmpeg_path="ffmpeg",
        input_file="in.mp4",
        palette_path="palette.png",
        fps=7,
        width=480,
        colors=128
    )
    assert cmd_palette == [
        "ffmpeg", "-y", "-hide_banner",
        "-i", "in.mp4",
        "-vf", "fps=7,scale=480:-2:flags=lanczos,palettegen=max_colors=128",
        "palette.png"
    ]
    
    cmd_render = command_builder.build_gif_render_command(
        ffmpeg_path="ffmpeg",
        input_file="in.mp4",
        palette_path="palette.png",
        output_file="out.gif",
        fps=7,
        width=480,
        dither="bayer:bayer_scale=3"
    )
    assert cmd_render == [
        "ffmpeg", "-y", "-hide_banner",
        "-i", "in.mp4",
        "-i", "palette.png",
        "-filter_complex", "fps=7,scale=480:-2:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
        "out.gif"
    ]
    
    cmd_gifsicle = command_builder.build_gifsicle_command(
        gifsicle_path="gifsicle",
        input_file="out.gif",
        output_file="out_opt.gif",
        colors=128,
        lossy=80
    )
    assert cmd_gifsicle == [
        "gifsicle", "-O3",
        "--lossy=80",
        "--colors", "128",
        "out.gif",
        "-o", "out_opt.gif"
    ]

def test_presets_file_loading(tmp_path):
    # Modifichiamo temporaneamente get_presets_path per puntare a una cartella temporanea
    test_file = tmp_path / "presets.json"
    
    # Se il file non esiste, lo crea al caricamento
    def dummy_get_path():
        return test_file
        
    original_get_presets_path = presets_manager.get_presets_path
    presets_manager.get_presets_path = dummy_get_path
    
    try:
        # Carica
        data, err = presets_manager.load_presets()
        assert err is None
        assert test_file.exists()
        assert data["schema_version"] == 1
        
        # Scrivi dati invalidi e verifica il fallback
        with open(test_file, 'w') as f:
            f.write("invalido json {")
            
        data_fallback, err_msg = presets_manager.load_presets()
        assert "Errore" in err_msg or "invalido" in err_msg
        assert data_fallback["schema_version"] == 1 # Fallback caricato
        
    finally:
        presets_manager.get_presets_path = original_get_presets_path
