# 🎬 FFmpeg GUI - Video Encoder

![Downloads](https://img.shields.io/github/downloads/gulp79/ffmpeg-gui/total)

A very simple graphical interface for FFmpeg with support for AV1, H265 and H264 encoding using CUDA hardware acceleration.

![FFmpeg GUI Screenshot](https://github.com/user-attachments/assets/99f838d6-08bf-4cdd-b23f-6d8f2aef75c1)

[![Latest Downloads](https://img.shields.io/github/downloads/gulp79/ffmpeg-gui/latest/total)](https://github.com/gulp79/ffmpeg-gui/releases) [![GitHub release](https://img.shields.io/github/v/release/gulp79/ffmpeg-gui?include_prereleases)](https://github.com/gulp79/ffmpeg-gui/releases/latest)

## ✨ Features

- **🎯 Modern UI**: Attractive dark‑mode design, intuitive layout.
- **⚡ Hardware Acceleration**: Full NVENC CUDA support.
- **📹 Multi‑Codec**: AV1, H265 (HEVC), H264 with configurable presets.
- **🔄 Scaling**: Automatic scaling to common resolutions (576p, 720p, 1080p, 1440p, 2160p).
- **👁️ Command Preview**: Shows the FFmpeg command before execution.
- **📊 Real‑time Log**: Streams FFmpeg output while encoding.
- **🎛️ Advanced Controls**: Presets, CQ/quality parameter, audio copy options.
- **🚀 Drag & Drop**: Drag files directly onto the interface (where supported).
- **🖼️ Animation Mode**: Create animated WebP, AVIF or GIF files from video clips.

## 🚀 Quick Start

### Option 1: Pre‑compiled executable (recommended)

1. Download the latest release from **[GitHub Releases](../../releases)**.
2. Extract the archive.
3. Ensure FFmpeg is installed (see *FFmpeg Installation* below).
4. Run `FFmpeg_GUI.exe`.

### Option 2: From source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tuousername/ffmpeg-gui.git
   cd ffmpeg-gui
   ```
2. **Set up the environment**:
   ```bash
   # Windows
   pip install -r requirements.txt

   # Linux/macOS
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python ffmpeg_gui.py
   ```

## 🛠️ Building

### Windows with Nuitka (converts Python code to C/C++ and compiles it)

1. **Build the executable**:
   ```batch
   pip install nuitka ordered-set
   nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --mingw64 --windows-icon-from-ico=icona.ico FFmpeg-GUI.py
   ```
2. **Output**:
   - `FFmpeg_GUI.exe` – the executable.

### Windows with PyInstaller (bundles Python interpreter and source into a single executable)

1. **Build the executable**:
   ```batch
   pip install pyinstaller
   pyinstaller --name FFmpeg-GUI --onefile --windowed --icon="icona.ico" FFmpeg-GUI.py
   ```
2. **Output**:
   - `dist/FFmpeg_GUI.exe` – the executable.

### Linux with PyInstaller

1. **Build the executable**:
   ```batch
   sudo apt install -y python3-tk tkdnd
   pip install pyinstaller
   pyinstaller --name FFmpeg-GUI --onefile --windowed FFmpeg-GUI.py
   ```
2. **Output**:
   - `dist/FFmpeg_GUI.bin` – the executable.

### Linux with Nuitka

1. **Build the executable**:
   ```batch
   sudo apt install -y python3-tk tkdnd
   pip install nuitka ordered-set
   python -m nuitka --standalone --onefile --enable-plugin=tk-inter FFmpeg-GUI.py
   ```
2. **Output**:
   - `FFmpeg_GUI.bin` – the executable.

## 📦 FFmpeg Installation

### Windows

**Option 1 – Automatic**:
```powershell
# With winget
winget install FFmpeg

# With chocolatey
choco install ffmpeg
```

**Option 2 – Manual**:
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html).
2. Extract to a folder (e.g. `C:\ffmpeg`).
3. Add `C:\ffmpeg\bin` to the system PATH, or copy `ffmpeg.exe` into the application folder.

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
# Homebrew
brew install ffmpeg

# MacPorts
sudo port install ffmpeg
```

## 🎮 Usage

The application offers two main operating modes via a segmented selector:

### 1. Video Mode (preset‑based)
- **Select Input File**: Click *Add File* or drag one or more video files onto the interface.
- **Select Preset**: Choose an encoding preset (e.g., `AV1 NVENC`, `H265 NVENC`, ...). Controls adapt dynamically to the selected preset.
- **Speed Preset**: Choose encoding speed (p1‑p7).
- **CQ / Quality**: Adjust the desired quality.
- **Scaling**: Choose to rescale the video (e.g., 1080p, 720p) or keep the original resolution.
- **Start**: Click *Start Compression*.

### 2. Animation Mode
Create animated clips from video files in the following formats:
- **Animated WebP** (`.webp`)
- **Animated AVIF** (`.avif`) – supports `libsvtav1` and `libaom‑av1` encoders.
- **Animated GIF** (`.gif`) – generates an optimized colour palette in a two‑pass process.

Configurable options in the GUI for animations:
- **FPS**: Set animation framerate (default: 7).
- **Maximum Width**: Scale to standard widths or specify a custom width ("Custom").
- **GIF Optimisation**: When enabled, the app looks for `gifsicle` on the system to further optimise the produced GIF.

---

## ⚙️ Preset Configuration (`presets.json`)

From this version onward, encoding presets are no longer hard‑coded; they are loaded from an external `presets.json` file.

### File location
The application searches for `presets.json` in the same directory as the script or the compiled executable (both Nuitka and PyInstaller builds). If the file does not exist, a default one is created automatically.

### Adding a custom preset (e.g., Xvid in AVI)
Simply insert a new object into the `"video_presets"` list in `presets.json`. Example:
```json
{
  "id": "xvid_avi",
  "name": "Compress Xvid",
  "description": "Software Xvid compression in an AVI container",
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
      "max": 31
    }
  }
}
```
