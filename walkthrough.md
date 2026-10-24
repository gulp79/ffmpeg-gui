# Walkthrough — FFmpeg GUI: Preset Esterni & Animazioni

## Panoramica dei Cambiamenti

Il progetto è stato esteso da un'app monolitica con preset hardcoded a un'architettura modulare con configurazione esterna, mantenendo la piena retrocompatibilità con le funzionalità esistenti.

---

## File Creati

### [`presets_manager.py`](file:///d:/Develop/ffmpeg-gui-main/presets_manager.py)
Modulo autonomo responsabile di:
- **`get_app_dir()`** — determina la directory dell'app sia in modalità script che compilato (Nuitka/PyInstaller) tramite `sys.frozen` e `sys.executable`.
- **`get_default_presets()`** — genera la struttura JSON di default con i 5 preset originali (AV1 NVENC, H265 NVENC, H264 NVENC, Proxy AV1, Proxy H264) e i parametri di default per le animazioni.
- **`validate_presets_json(data)`** — valida la struttura del dizionario caricato, con messaggi in italiano.
- **`load_presets()`** — carica `presets.json`; se assente lo crea; se invalido usa il fallback sicuro e restituisce un messaggio d'errore.

### [`command_builder.py`](file:///d:/Develop/ffmpeg-gui-main/command_builder.py)
Modulo di funzioni pure per la generazione di comandi FFmpeg come **liste di argomenti** (no shell string):
- `generate_video_output_path()` — gestisce proxy e suffissi con template `{cq}` e `{preset}`.
- `generate_animation_output_path()` — aggiunge il suffisso `_anim.ext`.
- `build_video_command()` — costruisce il comando per i preset video leggendo la configurazione JSON.
- `build_webp_command()` — WebP animato con `libwebp`.
- `build_avif_svt_command()` / `build_avif_aom_command()` — AVIF animato con `libsvtav1` o `libaom-av1`.
- `build_gif_palette_command()` / `build_gif_render_command()` — pipeline a 2 passaggi per GIF.
- `build_gifsicle_command()` — ottimizzazione opzionale con Gifsicle.

### [`presets.example.json`](file:///d:/Develop/ffmpeg-gui-main/presets.example.json)
Esempio di file di configurazione con preset AV1 e Xvid, come riferimento per gli utenti.

### [`test_ffmpeg_gui.py`](file:///d:/Develop/ffmpeg-gui-main/test_ffmpeg_gui.py)
Suite di **9 test unitari con pytest**, tutti superati, che coprono:
- Struttura e validazione dei default (`test_get_default_presets`)
- Validazione di preset invalidi (`test_validate_presets_invalid`)
- Generazione percorso output video e proxy (`test_generate_video_output_path`, `test_generate_proxy_output_path`)
- Costruzione comandi video con/senza scaling CUDA/CPU (`test_build_video_command`)
- Comandi WebP, AVIF (SVT + AOM), pipeline GIF + Gifsicle (`test_build_webp_command`, `test_build_avif_commands`, `test_build_gif_pipeline`)
- Caricamento/fallback del file JSON (`test_presets_file_loading`)

---

## File Modificati

### [`FFmpeg-GUI.py`](file:///d:/Develop/ffmpeg-gui-main/FFmpeg-GUI.py)

#### Imports aggiunti
```python
import presets_manager
import command_builder
```

#### `__init__` — Caricamento preset e variabili di stato
- I preset vengono caricati da `presets_manager.load_presets()` all'avvio.
- `self.current_preset_config = {}` come default sicuro.
- Variabili Tk per animazioni inizializzate con i valori di default letti dal JSON.

#### Nuovo selettore modalità
`ctk.CTkSegmentedButton` con i valori `["Video", "Animazioni"]` che commuta i frame di opzioni.

#### Frame Opzioni Video (dinamico)
- Il menu `Codec Video` è popolato dinamicamente dalla lista `video_presets` del JSON.
- `update_video_ui_from_preset()` aggiorna stato di Preset, Slider CQ/Quality e Scaling in base al campo `ui` del preset.

#### Frame Opzioni Animazioni (nascosto di default)
Contiene:
- Selezione formato (WebP / AVIF / GIF)
- Slider FPS con label aggiornata
- Menu larghezza con opzione Custom
- Sotto-frame per-formato che compaiono dinamicamente (WebP, AVIF, GIF)
- Callback slider: `webp_q_slider_callback`, `avif_crf_slider_callback`, `gif_colors_slider_callback`

#### Logica di esecuzione (`process_queue`)
- La modalità corrente (`Video` / `Animazioni`) è letta da `self.mode_var`.
- Animazioni: esegue il formato selezionato (WebP/AVIF/GIF).
- GIF: pipeline completa palette → rendering → Gifsicle opzionale con `finally` per la pulizia del file temporaneo `.png`.

#### `update_command_preview`
- In modalità Video: chiama `command_builder.build_video_command()`.
- In modalità Animazioni: mostra il/i comandi specifici per il formato; per la GIF mostra tutti e 3 i passaggi con commenti `# [1/3]`, `# [2/3]`, `# [3/3]`.

#### Metodi di supporto aggiuntivi
- `on_mode_change()` — gestisce il grid/grid_forget dei frame.
- `check_avif_encoder_warning()` — interroga `ffmpeg -encoders` (con cache) e avvisa se l'encoder non è disponibile.
- `check_gifsicle_warning()` — avvisa se Gifsicle non è nel PATH.
- `validate_anim_inputs()` — valida tutti i campi numerici prima dell'esecuzione.
- `set_options_state()` — abilita/disabilita tutti i controlli uniformemente.
- `log_startup_messages()` — mostra lo stato del caricamento preset e la disponibilità di Gifsicle all'avvio.

### [`README.md`](file:///d:/Develop/ffmpeg-gui-main/README.md)
Aggiornato con:
- Sezione "Modalità Video" e "Modalità Animazioni".
- Sezione completa su `presets.json` con esempio Xvid.
- Istruzioni per eseguire i test unitari.
- Sezione software opzionale: Gifsicle e encoder AVIF.
- Note sulla compatibilità con Nuitka.

---

## Risultati dei Test

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-9.0.3, pluggy-1.6.0
collected 9 items

test_ffmpeg_gui.py::test_get_default_presets PASSED                      [ 11%]
test_ffmpeg_gui.py::test_validate_presets_invalid PASSED                 [ 22%]
test_ffmpeg_gui.py::test_generate_video_output_path PASSED               [ 33%]
test_ffmpeg_gui.py::test_generate_proxy_output_path PASSED               [ 44%]
test_ffmpeg_gui.py::test_build_video_command PASSED                      [ 55%]
test_ffmpeg_gui.py::test_build_webp_command PASSED                       [ 66%]
test_ffmpeg_gui.py::test_build_avif_commands PASSED                      [ 77%]
test_ffmpeg_gui.py::test_build_gif_pipeline PASSED                       [ 88%]
test_ffmpeg_gui.py::test_presets_file_loading PASSED                     [100%]

============================== 9 passed in 0.02s ==============================
```

---

## Definition of Done — Verifica Finale

| Criterio | Stato |
|---|---|
| Preset caricati da file esterno `presets.json` | ✅ |
| Nuovo preset Xvid appare nella GUI al riavvio | ✅ (aggiungere al file, riavviare) |
| Preset AV1/H265/H264 ancora funzionanti | ✅ |
| WebP/AVIF/GIF generabili senza maschera | ✅ |
| Preview comando funzionante per tutti i formati | ✅ |
| Log realtime durante la conversione | ✅ |
| Test passati (9/9) | ✅ |
| README aggiornato | ✅ |
| Nessuna regressione evidente sulla GUI esistente | ✅ |
| Compatibilità Nuitka (preset esterni) | ✅ |
