# 🎬 FFmpeg GUI - Video Encoder

Una semplicissima interfaccia grafica per FFmpeg con supporto per codifica AV1, H265 e H264 con accelerazione hardware CUDA.

![FFmpeg GUI Screenshot](https://github.com/user-attachments/assets/6c34b84d-6cb2-4f4c-80f5-85891cf5f626)


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
   nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --windows-icon-from-ico=icona.ico FFmpeg-GUI.py
   ```

2. **Output**:
   - `FFmpeg_GUI.exe` - Eseguibile
   - 
### Windows con Pyinstaller (Impacchetta l'interprete Python, il tuo codice sorgente in un unico pacchetto eseguibile)

1. **Compila l'eseguibile**:
   ```batch
   pip install pyinstaller
   pyinstaller --name FFmpeg-GUI --onefile --windowed --icon="icona.ico" FFmpeg-GUI.py
   ```

2. **Output**:
   - `dist/FFmpeg_GUI.exe` - Eseguibile
   - 

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

1. **Seleziona File Input**: Click su "Sfoglia..." o trascina un file video
2. **Configura Codec**: Scegli tra AV1, H265, H264
3. **Imposta Preset**: Seleziona da p1 (veloce) a p7 (qualità)
4. **CQ Parameter**: 0-51, dove 0 = auto, 1=lossless, 51 = qualità minima
5. **Risoluzione**: Scegli il ridimensionamento o mantieni originale
6. **File Output**: Lascia vuoto per nome automatico o specifica un percorso
7. **Avvia Codifica**: Click su "🚀 Avvia Codifica"

### Esempi di Comandi Generati

**AV1 1080p CQ18**:
```bash
ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i "input.mp4" -vf "scale_cuda=-2:1080" -c:v av1_nvenc -preset p4 -rc:v vbr -cq:v 18 -rc-lookahead 32 -spatial-aq 1 -temporal-aq 1 -c:a copy "output_av1_cq18.mp4"
```

**H265 720p CQ23**:
```bash
ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i "input.mp4" -vf "scale_cuda=-2:720" -c:v hevc_nvenc -preset p6 -rc:v vbr_hq -cq:v 23 -rc-lookahead 32 -spatial-aq 1 -temporal-aq 1 -c:a copy "output_h265_cq23.mp4"
```

## ⚙️ Requisiti di Sistema

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

## 🔧 Configurazione Avanzata

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
