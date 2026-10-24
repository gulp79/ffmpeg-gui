# 🎬 FFmpeg GUI - Video Encoder
![Downloads](https://img.shields.io/github/downloads/gulp79/ffmpeg-gui/total)

Una semplicissima interfaccia grafica per FFmpeg con supporto per codifica AV1, H265 e H264 con accelerazione hardware CUDA.

![FFmpeg GUI Screenshot](https://github.com/user-attachments/assets/99f838d6-08bf-4cdd-b23f-6d8f2aef75c1)

[![Latest Downloads](https://img.shields.io/github/downloads/gulp79/ffmpeg-gui/latest/total
)](https://github.com/gulp79/ffmpeg-gui/releases) [![GitHub release](https://img.shields.io/github/v/release/gulp79/ffmpeg-gui?include_prereleases)](https://github.com/gulp79/ffmpeg-gui/releases/latest)

## ✨ Caratteristiche

- **🎯 Interfaccia Moderna**: Design dark mode accattivante e intuitivo
- **⚡ Accelerazione Hardware**: Supporto completo per NVENC CUDA
- **📹 Multi-Codec**: AV1, H265 (HEVC), H264 con preset configurabili
- **🔄 Ridimensionamento**: Scaling automatico a risoluzioni comuni (576p, 720p, 1080p, 1440p, 2160p)
- **👁️ Anteprima Comando**: Visualizza il comando FFmpeg prima dell'esecuzione
- **📊 Log in Tempo Reale**: Monitor dell'output FFmpeg durante la codifica
- **🎛️ Controlli Avanzati**: Preset, CQ parameter, e opzioni audio copy
- **🚀 Drag & Drop**: Trascina i file direttamente nell'interfaccia (dove supportato)

## 🚀 Quick Start

### Opzione 1: Eseguibile Pre-compilato (Consigliato)

1. Scarica l'ultima release da [GitHub Releases](../../releases)
2. Estrai l'archivio
3. Assicurati che FFmpeg sia installato (vedi [Installazione FFmpeg](#-installazione-ffmpeg))
4. Esegui `FFmpeg_GUI.exe`

### Opzione 2: Da Codice Sorgente

1. **Clona il repository**:
   ```bash
   git clone https://github.com/tuousername/ffmpeg-gui.git
   cd ffmpeg-gui
   ```

2. **Setup ambiente**:
   ```bash
   # Windows
   pip install -r requirements.txt
   
   # Linux/macOS
   pip install -r requirements.txt
   ```

3. **Esegui l'applicazione**:
   ```bash
   python ffmpeg_gui.py
   ```

## 🛠️ Compilazione

### Windows con Nuitka (Coverte il codice Python in C o C++ che poi viene compilato)

1. **Compila l'eseguibile**:
   ```batch
   pip install nuitka ordered-set
   nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --mingw64 --windows-icon-from-ico=icona.ico FFmpeg-GUI.py
   ```

2. **Output**:
   - `FFmpeg_GUI.exe` - Eseguibile
     
### Windows con Pyinstaller (Impacchetta l'interprete Python, il tuo codice sorgente in un unico pacchetto eseguibile)

1. **Compila l'eseguibile**:
   ```batch
   pip install pyinstaller
   pyinstaller --name FFmpeg-GUI --onefile --windowed --icon="icona.ico" FFmpeg-GUI.py
   ```

2. **Output**:
   - `dist/FFmpeg_GUI.exe` - Eseguibile
   -
### Linux con Pyinstaller (Impacchetta l'interprete Python, il tuo codice sorgente in un unico pacchetto eseguibile)

1. **Compila l'eseguibile**:
   ```batch
   sudo apt install -y python3-tk tkdnd
   pip install pyinstaller
   pyinstaller --name FFmpeg-GUI --onefile --windowed FFmpeg-GUI.py
   ```

2. **Output**:
   - `dist/FFmpeg_GUI.bin` - Eseguibile
   
### Linux con Nuitka (Coverte il codice Python in C o C++ che poi viene compilato)

1. **Compila l'eseguibile**:
   ```batch
   sudo apt install -y python3-tk tkdnd
   pip install nuitka ordered-set
   python -m nuitka --standalone --onefile --enable-plugin=tk-inter FFmpeg-GUI.py
   ```

2. **Output**:
   - `FFmpeg_GUI.bin` - Eseguibile

## 📦 Installazione FFmpeg

### Windows

**Opzione 1 - Automatica**:
```powershell
# Con winget
winget install FFmpeg

# Con chocolatey
choco install ffmpeg
```

**Opzione 2 - Manuale**:
1. Scarica da [ffmpeg.org](https://ffmpeg.org/download.html)
2. Estrai in una cartella (es. `C:\ffmpeg`)
3. Aggiungi `C:\ffmpeg\bin` al PATH del sistema
4. Oppure copia `ffmpeg.exe` nella cartella dell'applicazione

### Linux

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL/Fedora
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### macOS

```bash
# Con Homebrew
brew install ffmpeg

# Con MacPorts
sudo port install ffmpeg
```

## 🎮 Utilizzo

L'applicazione supporta due modalità operative principali tramite un selettore segmentato:

### 1. Modalità Video (basata su preset esterni)
- **Seleziona File Input**: Clicca su "Aggiungi File" o trascina uno o più file video nell'interfaccia.
- **Seleziona Preset**: Scegli il preset di codifica (es. `AV1 NVENC`, `H265 NVENC`, ecc.). I controlli si adatteranno dinamicamente abilitando solo le opzioni supportate dal preset.
- **Preset Velocità**: Scegli la velocità di codifica (da p1 a p7).
- **CQ / Qualità**: Regola la qualità desiderata.
- **Ridimensionamento**: Scegli se riscalare il video (es. 1080p, 720p) o mantenere la risoluzione originale.
- **Avvia**: Clicca su "Avvia Compressione".

### 2. Modalità Animazioni
Consente di generare clip animate a partire da video, nei formati:
- **WebP animato** (`.webp`)
- **AVIF animato** (`.avif`): supporta gli encoder `libsvtav1` e `libaom-av1`.
- **GIF animata** (`.gif`): genera una palette colori ottimizzata in 2 passaggi.

Opzioni configurabili nella GUI:
- **FPS**: Regola il framerate dell'animazione (default: 7).
- **Larghezza Max**: Riscala a larghezze standard o specifica una larghezza personalizzata ("Custom").
- **Ottimizzazione GIF**: Se abilitata, l'applicazione cercherà l'eseguibile `gifsicle` nel sistema per ottimizzare e comprimere ulteriormente la GIF prodotta.

---

## ⚙️ Configurazione dei Preset (presets.json)

A partire da questa versione, i preset di encoding non sono più scritti nel codice, ma vengono caricati da un file esterno chiamato `presets.json`.

### Posizione del file
L'applicazione cerca `presets.json` nella stessa directory in cui risiede lo script o l'eseguibile compilato (sia con Nuitka che con PyInstaller). Se il file non esiste, ne viene creato uno automaticamente con i preset di default.

### Aggiungere un preset personalizzato (es. Xvid in AVI)
È sufficiente inserire un nuovo oggetto all'interno della lista `"video_presets"` nel file `presets.json`. Ecco un esempio di preset Xvid:

```json
{
  "id": "xvid_avi",
  "name": "Comprimi Xvid",
  "description": "Compressione software Xvid in container AVI",
  "category": "video",
  "output_extension": ".avi",
  "output_suffix": "_xvid",
  "ffmpeg": {
    "hwaccel": [],
    "video_codec": ["-c:v", "libxvid"],
    "rate_control": [],
    "quality_template": ["-q:v", "{quality}"],
    "preset_template": [],
    "extra_video_args": [],
    "container_args": [],
    "audio_args": ["-c:a", "libmp3lame", "-q:a", "4"]
  },
  "ui": {
    "quality": {
      "enabled": true,
      "default": 4,
      "min": 1,
      "max": 31,
      "label": "Qualità Xvid q:v"
    },
    "scale": {
      "enabled": true
    }
  }
}
```

Al successivo avvio dell'applicazione, il preset "Comprimi Xvid" apparirà automaticamente nel menu a tendina.

---

## 🧪 Esecuzione dei Test Unitari

Per validare la generazione dei comandi e il comportamento del parser dei preset, puoi eseguire la suite di test unitari con `pytest`:

```powershell
pip install pytest
pytest test_ffmpeg_gui.py -v
```

---

## ⚙️ Requisiti di Sistema e Software Opzionale

### Minimi
- **OS**: Windows 10+, Linux, macOS 10.14+
- **Python**: 3.8+ (solo per sviluppo)
- **RAM**: 4GB
- **Storage**: 100MB per l'applicazione

### Raccomandati per Prestazioni Ottimali
- **GPU**: NVIDIA GTX 1060+ con driver aggiornati
- **RAM**: 8GB+
- **CPU**: Intel i5/AMD Ryzen 5 o superiore
- **CUDA**: Toolkit 11.0+ per accelerazione hardware

### Software Opzionale

#### Gifsicle (ottimizzazione GIF)
[Gifsicle](https://www.lcdf.org/gifsicle/) è un tool a riga di comando per ottimizzare le GIF animate. Se installato e presente nel `PATH`, l'applicazione lo utilizzerà automaticamente come terzo passaggio nella pipeline di generazione GIF.

```powershell
# Windows (con Chocolatey)
choco install gifsicle

# Linux (Ubuntu/Debian)
sudo apt install gifsicle

# macOS (con Homebrew)
brew install gifsicle
```

Se Gifsicle non è trovato, la GIF viene comunque prodotta correttamente senza ottimizzazione.

#### Encoder AVIF in FFmpeg
La generazione di AVIF animato richiede che la build di FFmpeg in uso includa uno dei seguenti encoder:
- **`libsvtav1`** *(consigliato)*: encoder SVT-AV1, molto più veloce, raccomandato per uso generale.
- **`libaom-av1`**: encoder di riferimento libaom, più lento ma molto stabile.

Per verificare gli encoder disponibili nella propria build di FFmpeg:
```bash
ffmpeg -encoders | findstr av1
```

Al momento della selezione del formato AVIF nella GUI, l'applicazione verificherà automaticamente la disponibilità dell'encoder scelto e mostrerà un avviso se non è supportato.

### Note sulla Compatibilità con Nuitka
Il file `presets.json` viene sempre letto dalla cartella dell'**eseguibile compilato**, non è incorporato nell'eseguibile. Questo consente di modificare i preset senza ricompilare l'applicazione.



### Variabili d'Ambiente

```bash
# Specifica path FFmpeg personalizzato
export FFMPEG_PATH="/path/to/custom/ffmpeg"

# Debug mode
export FFMPEG_GUI_DEBUG=1
```

### File di Configurazione

L'applicazione cerca FFmpeg in questo ordine:
1. Variabile d'ambiente `FFMPEG_PATH`
2. Cartella dell'applicazione (`./ffmpeg.exe`)
3. PATH del sistema

## 🤝 Contribuire

1. **Fork** il repository
2. **Crea** un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** le modifiche (`git commit -m 'Add some AmazingFeature'`)
4. **Push** al branch (`git push origin feature/AmazingFeature`)
5. **Apri** una Pull Request

### Sviluppo Locale

```bash
# Clone e setup
git clone https://github.com/tuousername/ffmpeg-gui.git
cd ffmpeg-gui

# Ambiente virtuale (raccomandato)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# oppure
venv\Scripts\activate     # Windows

# Installa dipendenze
pip install -r requirements.txt

# Esegui in modalità sviluppo
python ffmpeg_gui.py
```

## 📋 TODO & Roadmap

- [ ] **Profili Personalizzati**: Salva e carica configurazioni
- [ ] **Anteprima Video**: Preview del file di input
- [ ] **Supporto GPU AMD**: Encoder VCE/AMF
- [ ] **Filtri Video**: Crop, rotate, deinterlace
- [ ] **Audio Settings**: Codec, bitrate, channels
- [ ] **Subtitle Support**: Embed/extract sottotitoli
- [ ] **Network Streams**: Input da URL/streaming
- [ ] **Localizzazione**: Interfaccia multilingue

## 🐛 Risoluzione Problemi

### FFmpeg non trovato
```
❌ FFmpeg non trovato nel PATH o nella cartella locale
```
**Soluzione**: Installa FFmpeg o copialo nella cartella dell'app

### Errore CUDA
```
❌ CUDA initialization failed
```
**Soluzioni**:
- Aggiorna driver NVIDIA
- Verifica compatibilità GPU
- Usa encoder software (`-c:v libx264`)

### Dipendenze Python
```
❌ ModuleNotFoundError: No module named 'customtkinter'
```
**Soluzione**:
```bash
pip install -r requirements.txt
```

### Permessi File
```
❌ Permission denied writing output file
```
**Soluzioni**:
- Esegui come amministratore
- Cambia cartella di output
- Verifica permessi file

## 📊 Performance

### Benchmark Tipici (GTX 1080)

| Codec | Risoluzione | Preset | FPS | Qualità |
|-------|-------------|---------|-----|---------|
| H264  | 1080p       | p4      | 120 | Ottima  |
| H265  | 1080p       | p4      | 80  | Eccellente |
| AV1   | 1080p       | p4      | 25  | Superiore |

*I risultati possono variare in base all'hardware e al contenuto*

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi `LICENSE` per dettagli.

## 🙏 Ringraziamenti

- **FFmpeg Team** - Per l'incredibile strumento di encoding
- **CustomTkinter** - Per la moderna UI framework
- **NVIDIA** - Per l'accelerazione hardware NVENC
- **Community** - Per feedback e contributi

## 📞 Supporto

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)
- **Email**: your-email@example.com

---

⭐ **Se questo progetto ti è stato utile, lascia una stella!** ⭐
