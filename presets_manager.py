import os
import sys
import json
from pathlib import Path

SCHEMA_VERSION = 1

def get_app_dir() -> Path:
    """
    Ritorna la directory dell'applicazione, gestendo la compatibilità
    sia per lo script Python che per l'eseguibile compilato (con Nuitka o PyInstaller).
    """
    # Se compilato (Nuitka o PyInstaller), sys.executable punta all'eseguibile
    if getattr(sys, 'frozen', False) or hasattr(sys, 'is_nuitka') or (module := sys.modules.get('__main__')) and not hasattr(module, '__file__'):
        return Path(os.path.dirname(os.path.abspath(sys.executable)))
    
    try:
        return Path(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        return Path(os.path.dirname(os.path.abspath(sys.argv[0])))

def get_presets_path() -> Path:
    """Ritorna il percorso completo del file presets.json."""
    return get_app_dir() / "presets.json"

def get_default_presets() -> dict:
    """Genera la configurazione di default contenente i preset originali dell'app."""
    return {
        "schema_version": SCHEMA_VERSION,
        "video_presets": [
            {
                "id": "av1_nvenc",
                "name": "AV1 NVENC",
                "description": "Encoding AV1 con accelerazione NVIDIA NVENC",
                "category": "video",
                "output_extension": None,
                "output_suffix": "_AV1_CQ{cq}",
                "ffmpeg": {
                    "hwaccel": ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
                    "video_codec": ["-c:v", "av1_nvenc"],
                    "rate_control": ["-rc", "vbr"],
                    "quality_template": ["-cq", "{cq}"],
                    "preset_template": ["-preset", "{preset}"],
                    "extra_video_args": [
                        "-b:v", "0",
                        "-tune", "hq",
                        "-rc-lookahead", "64",
                        "-spatial-aq", "1",
                        "-temporal-aq", "1",
                        "-g", "120",
                        "-bf", "2"
                    ],
                    "container_args": ["-movflags", "+faststart"],
                    "audio_args": ["-c:a", "copy"]
                },
                "ui": {
                    "cq": {
                        "enabled": True,
                        "default": 0,
                        "min": 0,
                        "max": 51
                    },
                    "preset": {
                        "enabled": True,
                        "default": "p6",
                        "options": ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]
                    },
                    "scale": {
                        "enabled": True
                    }
                }
            },
            {
                "id": "hevc_nvenc",
                "name": "H265 NVENC",
                "description": "Encoding H265/HEVC con accelerazione NVIDIA NVENC",
                "category": "video",
                "output_extension": None,
                "output_suffix": "_H265_CQ{cq}",
                "ffmpeg": {
                    "hwaccel": ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
                    "video_codec": ["-c:v", "hevc_nvenc"],
                    "rate_control": ["-rc", "vbr_hq"],
                    "quality_template": ["-cq", "{cq}"],
                    "preset_template": ["-preset", "{preset}"],
                    "extra_video_args": [
                        "-b:v", "0",
                        "-tune", "hq",
                        "-rc-lookahead", "64",
                        "-spatial-aq", "1",
                        "-temporal-aq", "1",
                        "-g", "120",
                        "-bf", "2"
                    ],
                    "container_args": ["-movflags", "+faststart"],
                    "audio_args": ["-c:a", "copy"]
                },
                "ui": {
                    "cq": {
                        "enabled": True,
                        "default": 0,
                        "min": 0,
                        "max": 51
                    },
                    "preset": {
                        "enabled": True,
                        "default": "p6",
                        "options": ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]
                    },
                    "scale": {
                        "enabled": False
                    }
                }
            },
            {
                "id": "h264_nvenc",
                "name": "H264 NVENC",
                "description": "Encoding H264 con accelerazione NVIDIA NVENC",
                "category": "video",
                "output_extension": None,
                "output_suffix": "_H264_CQ{cq}",
                "ffmpeg": {
                    "hwaccel": ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
                    "video_codec": ["-c:v", "h264_nvenc"],
                    "rate_control": ["-rc", "vbr_hq"],
                    "quality_template": ["-cq", "{cq}"],
                    "preset_template": ["-preset", "{preset}"],
                    "extra_video_args": [
                        "-b:v", "0",
                        "-tune", "hq",
                        "-rc-lookahead", "64",
                        "-spatial-aq", "1",
                        "-temporal-aq", "1",
                        "-g", "120",
                        "-bf", "2"
                    ],
                    "container_args": ["-movflags", "+faststart"],
                    "audio_args": ["-c:a", "copy"]
                },
                "ui": {
                    "cq": {
                        "enabled": True,
                        "default": 0,
                        "min": 0,
                        "max": 51
                    },
                    "preset": {
                        "enabled": True,
                        "default": "p6",
                        "options": ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]
                    },
                    "scale": {
                        "enabled": False
                    }
                }
            },
            {
                "id": "proxy_av1",
                "name": "Proxy AV1",
                "description": "Crea proxy AV1 a bassa risoluzione (576p)",
                "category": "video",
                "output_extension": None,
                "output_suffix": "",
                "ffmpeg": {
                    "hwaccel": ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
                    "video_codec": ["-c:v", "av1_nvenc"],
                    "rate_control": [],
                    "quality_template": ["-cq", "0"],
                    "preset_template": ["-preset", "p1"],
                    "extra_video_args": [
                        "-vf", "scale_cuda=-2:576",
                        "-tune", "ll",
                        "-g", "30"
                    ],
                    "container_args": [],
                    "audio_args": ["-c:a", "copy"]
                },
                "ui": {
                    "cq": {
                        "enabled": False
                    },
                    "preset": {
                        "enabled": False
                    },
                    "scale": {
                        "enabled": False
                    }
                }
            },
            {
                "id": "proxy_h264",
                "name": "Proxy H264",
                "description": "Crea proxy H264 a bassa risoluzione (576p)",
                "category": "video",
                "output_extension": None,
                "output_suffix": "",
                "ffmpeg": {
                    "hwaccel": ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
                    "video_codec": ["-c:v", "h264_nvenc"],
                    "rate_control": [],
                    "quality_template": ["-cq", "0"],
                    "preset_template": ["-preset", "p1"],
                    "extra_video_args": [
                        "-vf", "scale_cuda=-2:576",
                        "-tune", "ll",
                        "-g", "30"
                    ],
                    "container_args": [],
                    "audio_args": ["-c:a", "copy"]
                },
                "ui": {
                    "cq": {
                        "enabled": False
                    },
                    "preset": {
                        "enabled": False
                    },
                    "scale": {
                        "enabled": False
                    }
                }
            }
        ],
        "animation_presets": {
            "defaults": {
                "fps": 15,
                "target_width": 1920,
                "width_options": [1920, 1280, 720],
                "webp_quality": 70,
                "webp_method": 6,
                "avif_crf": 32,
                "avif_preset": 6,
                "avif_encoder": "libsvtav1",
                "gif_colors": 64,
                "gif_lossy": 100,
                "gif_dither": "bayer:bayer_scale=3"
            }
        }
    }

def validate_presets_json(data: dict) -> tuple[bool, str]:
    """
    Valida la struttura del dizionario caricato dal JSON.
    Ritorna una tupla (valido: bool, messaggio_errore: str).
    """
    if not isinstance(data, dict):
        return False, "Il contenuto principale del file deve essere un oggetto JSON."
    if "schema_version" not in data:
        return False, "Campo obbligatorio 'schema_version' mancante."
    if "video_presets" not in data or not isinstance(data["video_presets"], list):
        return False, "Il campo 'video_presets' deve essere una lista."
    
    for idx, preset in enumerate(data["video_presets"]):
        if not isinstance(preset, dict):
            return False, f"Il preset all'indice {idx} non è un oggetto JSON."
        for field in ("id", "name", "ffmpeg", "ui"):
            if field not in preset:
                return False, f"Nel preset video '{preset.get('name', idx)}' manca il campo obbligatorio '{field}'."
        
        ffmpeg = preset["ffmpeg"]
        if not isinstance(ffmpeg, dict):
            return False, f"Il campo 'ffmpeg' del preset '{preset['name']}' deve essere un oggetto."
        
        # Validiamo le chiavi necessarie del comando ffmpeg
        for list_field in ("hwaccel", "video_codec", "extra_video_args", "audio_args"):
            if list_field not in ffmpeg or not isinstance(ffmpeg[list_field], list):
                return False, f"Nel preset '{preset['name']}', il campo 'ffmpeg.{list_field}' deve essere una lista."
        
        ui = preset["ui"]
        if not isinstance(ui, dict):
            return False, f"Il campo 'ui' del preset '{preset['name']}' deve essere un oggetto."

    if "animation_presets" not in data or not isinstance(data["animation_presets"], dict):
        return False, "Il campo 'animation_presets' deve essere un oggetto."
    
    anim_defaults = data["animation_presets"].get("defaults", {})
    if not isinstance(anim_defaults, dict):
        return False, "Il campo 'animation_presets.defaults' deve essere un oggetto."
        
    return True, ""

def load_presets() -> tuple[dict, str | None]:
    """
    Carica i preset da presets.json. Se il file non esiste, lo crea con i default.
    Se è invalido, ritorna la configurazione di default (fallback sicuro) e un messaggio d'errore.
    Ritorna una tupla (configurazione: dict, messaggio_errore: str | None).
    """
    path = get_presets_path()
    
    # Se il file non esiste, crealo con i default
    if not path.exists():
        try:
            default_data = get_default_presets()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4, ensure_ascii=False)
            return default_data, None
        except Exception as e:
            return get_default_presets(), f"Impossibile creare presets.json di default: {e}"

    # Carica e valida il file esistente
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        valido, err_msg = validate_presets_json(data)
        if not valido:
            return get_default_presets(), f"File presets.json non valido strutturalmente: {err_msg}. Sarà usata la configurazione di fallback."
            
        return data, None
    except json.JSONDecodeError as e:
        return get_default_presets(), f"Errore di sintassi JSON in presets.json: {e}. Sarà usata la configurazione di fallback."
    except Exception as e:
        return get_default_presets(), f"Errore durante la lettura di presets.json: {e}. Sarà usata la configurazione di fallback."
